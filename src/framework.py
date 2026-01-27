import hashlib
import json
import logging
import os
import sys
from subprocess import PIPE, run

from src.bug import Bug
from src.utils import insert_method
from prog_params import ProgParams as prog_params
from src.get_test_info import get_test_function
from user_params import UserParams as user_params


class Framework(object):
    def __init__(self, name, list_of_bugs, d4j_path, java_home, tmp_dir, 
                 bug_details_cache_folder=None, validate_patch_cache_folder=None, n_shot_cache_folder=None):
        assert name in ["defects4j", "humanevaljava"]
        self.name = name
        self.list_of_bugs = list_of_bugs
        self.validate_patch_cache_folder = validate_patch_cache_folder
        self.n_shot_cache_folder = n_shot_cache_folder
        self.d4j_path = d4j_path
        self.java_home = java_home
        self.tmp_dir = tmp_dir
        self.bug_details_cache_folder = bug_details_cache_folder

        self.shell_script_folder = prog_params.shell_script_folder

    def get_bug_details(self, project, bug_id):
        if self.bug_details_cache_folder is not None:
            adapt_dir = self.bug_details_cache_folder
            if not os.path.exists(adapt_dir):
                os.makedirs(adapt_dir)
            file_path = f"{adapt_dir}/{project}-{bug_id}.json"
            if os.path.isfile(file_path):
                logging.debug(f"Retrieving bug details from cache (project={project}, bug_id={bug_id})")
                with open(file_path, "r") as f:
                    bug_details = json.load(f)
                return Bug(**bug_details)

        logging.debug(f"Checking out bug (project={project}, bug_id={bug_id}))")
        self.run_bash("checkout_bug", project, bug_id)

        bug_type = self.run_bash("get_bug_type", project, bug_id).stdout if self.name == "defects4j" else "BF"
        test_suite, test_name, test_error, test_line, buggy_lines, fixed_lines, code, masked_code, fixed_code, test_function =\
            None, None, None, None, None, None, None, None, None, None
        if bug_type not in ["OT", "BF"]:
            logging.debug(f"Compiling and running tests")
            self.run_bash("compile_and_run_tests", project, bug_id)
            logging.debug(f"Retreiving test suite")
            test_suite = self.run_bash("get_test_suite", project, bug_id).stdout
            logging.debug(f"Retreiving test name")
            test_name = self.run_bash("get_test_name", project, bug_id).stdout
            logging.debug(f"Retreiving test function")
            test_function = get_test_function(project, bug_id, test_suite, test_name)
            logging.debug(f"Retreiving test error message")
            test_error = self.run_bash("get_test_error", project, bug_id).stdout
            logging.debug(f"Retreiving test line")
            test_line = self.run_bash("get_test_line", project, bug_id).stdout
            logging.debug(f"Retreiving buggy lines")
            buggy_lines = self.run_bash("get_buggy_lines", project, bug_id).stdout
            logging.debug(f"Retreiving fixed lines")
            fixed_lines = self.run_bash("get_fixed_lines", project, bug_id).stdout
            logging.debug(f"Retreiving code")
            code = self.run_bash("get_code", project, bug_id).stdout
            logging.debug(f"Retreiving masked code")
            masked_code = self.run_bash("get_masked_code", project, bug_id).stdout
            logging.debug(f"Retreiving fixed code")
            fixed_code = self.run_bash("get_fixed_code", project, bug_id).stdout
        elif bug_type == "BF":
            logging.debug(f"Compiling and running tests")
            self.run_bash("compile_and_run_tests", project, bug_id)
            logging.debug(f"Retreiving test suite")
            test_suite = self.run_bash("get_test_suite", project, bug_id).stdout
            logging.debug(f"Retreiving test name")
            test_name = self.run_bash("get_test_name", project, bug_id).stdout
            logging.debug(f"Retreiving test function")
            test_function = get_test_function(project, bug_id, test_suite, test_name)
            logging.debug(f"Retreiving test error message")
            test_error = self.run_bash("get_test_error", project, bug_id).stdout
            logging.debug(f"Retreiving test line")
            test_line = self.run_bash("get_test_line", project, bug_id).stdout

        bug = Bug(test_suite=test_suite, test_name=test_name, test_line=test_line, test_error_message=test_error,
                  buggy_lines=buggy_lines, fixed_lines=fixed_lines, code=code, masked_code=masked_code, fixed_code=fixed_code,
                  test_framework=self.name, project=project, bug_id=bug_id, bug_type=bug_type, test_function=test_function)

        if self.bug_details_cache_folder is not None:
            with open(file_path, 'w') as f:
                vars_object = vars(bug)
                f.write(json.dumps(vars_object, indent=4, sort_keys=True))

        return bug

    def validate_patch(self, bug: Bug, proposed_patch: str, mode: str):
        assert mode in ["SL", "SH", "SF", "BF"]

        test_result = None
        result_reason = None
        patch_hash = hashlib.md5(str(proposed_patch).encode('utf-8')).hexdigest()

        if self.validate_patch_cache_folder is not None:
            adapt_dir = self.validate_patch_cache_folder
            if not os.path.exists(adapt_dir):
                os.makedirs(adapt_dir)
            cache_file_path = f"{adapt_dir}/{self.name}_{bug.project}_{bug.bug_id}_{mode}_{patch_hash}.json"
            if os.path.isfile(cache_file_path):
                with open(cache_file_path, "r") as file:
                    json_to_load = json.load(file)
                    test_result = json_to_load['test_result']
                    result_reason = json_to_load['result_reason']
                    patch_diff = json_to_load['patch_diff']
                logging.info(f"Retrieved test result from cache: {patch_hash}")

        if test_result is None and result_reason is None:

            project = bug.project
            bug_id = bug.bug_id
            
            self.run_bash("checkout_bug", bug.project, bug.bug_id)
            special = { 'Closure': [11, 66, 123],
                        'Gson': [6],
                        'JacksonCore': [15, 21, 23],
                        'JacksonDatabind': [19, 26],
                        'Jsoup': [15, 35, 38, 62, 76],
                        'Lang': [31],
                        'Mockito': [18]}
            if mode == "BF":
                path = self.run_bash("get_source_code_file_path", project, bug_id).stdout
                with open(path, "w", encoding='utf-8') as file:
                    file.write(proposed_patch)
                result = self.run_bash("compile_and_run_tests", project, bug_id, proposed_patch, mode)
            elif bug.code == "" and bug.buggy_lines == "": # If it needs to add an entire function without deleting anything
                path = self.run_bash("get_source_code_file_path", project, bug_id).stdout
                if path != "":
                    insert_method(proposed_patch, path)
                else:
                    logging.debug(f"Debug: project:{project}, bug_id: {bug_id}, proposed_patch: {proposed_patch}, mode: {mode}, path: {path}")
                result = self.run_bash("compile_and_run_tests", project, bug_id, proposed_patch, mode)
            elif bug.project in special.keys() and int(bug.bug_id) in special[bug.project]:
                info = prog_params.program_dir + '/special_validate/info.json'
                with open(info, "r", encoding='utf-8') as file:
                    path = user_params.D4J_TMP_DIR + json.load(file)[f'{bug.project}-{bug.bug_id}']
                json_dir = prog_params.program_dir + f'/special_validate/{bug.project}-{bug.bug_id}.json'
                with open(json_dir, "r", encoding='utf-8') as file:
                    json_to_load = json.load(file)
                    front = json_to_load['front']
                    behind = json_to_load['behind']
                    if mode == 'SL' or mode == 'SH':
                        proposed_patch = json_to_load['func_front']+proposed_patch+json_to_load['func_behind']
                    code = front+proposed_patch+behind
                with open(path, "w", encoding='utf-8') as file:
                    file.write(code)
                result = self.run_bash("compile_and_run_tests", project, bug_id, proposed_patch, mode)
            else:
                result = self.run_bash("validate_patch", project, bug_id, proposed_patch, mode)
                if "BUILD FAILED" in result.stderr and ">>> [ INFILL ] <<<" in result.stderr: # Check if >>> [ INFILL ] <<< in patch file
                    path = self.run_bash("get_source_code_file_path", project, bug_id).stdout
                    self.replace_infill(path)
                    result = self.run_bash("compile_and_run_tests", project, bug_id, proposed_patch, mode)
            patch_diff = self.run_bash("get_patch_git_diff", bug.project, bug.bug_id).stdout

            if bug.test_framework == "humanevaljava":
                # Compilation Error
                if "BUILD FAILURE" in result.stdout and "COMPILATION ERROR" in result.stdout:
                    stderr_lines = result.stdout.split("\n")
                    build_failed_line_i = next((i for i, line in enumerate(stderr_lines) if "COMPILATION ERROR" in line), None)
                    result_reason = stderr_lines[build_failed_line_i+2]
                    result_reason = result_reason[result_reason.find(' '):]
                    test_result, result_reason = "ERROR", result_reason
                # Test failure
                elif "BUILD FAILURE" in result.stdout:
                    test_result = "FAIL" # test fail
                    result_reason = self.run_bash("get_test_error", project, bug_id).stdout
                # Test pass
                elif "BUILD SUCCESS" in result.stdout:
                    test_result, result_reason = "PASS", "all tests passed"
                # Timeout
                else:
                    test_result, result_reason = "ERROR", "Test timed out after 600 seconds"
            elif bug.test_framework == "defects4j":
                if result.returncode != 0:
                    if result.stderr.find("error: ") > 0:
                        result_reason = result.stderr
                        result_reason = result_reason[result_reason.find("error: "):]
                        result_reason = result_reason[:result_reason.find("\n")]
                    elif "BUILD FAILED" in result.stderr:
                        stderr_lines = result.stderr.split("\n")
                        # line number of line that contains "BUILD FAILED"
                        build_failed_line_i = next((i for i, line in enumerate(stderr_lines) if "BUILD FAILED" in line), None)
                        result_reason = stderr_lines[build_failed_line_i+1]
                        result_reason = result_reason[result_reason.find(' '):]
                    else:
                        result_reason = "Test timed out after 600 seconds"
                    test_result, result_reason = "ERROR", result_reason # compilation error
                else:
                    all_tests_passed = result.stdout.find("Failing tests: 0") != -1
                    if all_tests_passed:
                        test_result, result_reason = "PASS", "all tests passed" # test pass
                    elif result.stderr.find("error: ") > 0:
                        result_reason = result.stderr
                        result_reason = result_reason[result_reason.find("error: "):]
                        result_reason = result_reason[:result_reason.find("\n")]
                        test_result = "ERROR"
                    elif "BUILD FAILED" in result.stderr:
                        stderr_lines = result.stderr.split("\n")
                        # line number of line that contains "BUILD FAILED"
                        build_failed_line_i = next((i for i, line in enumerate(stderr_lines) if "BUILD FAILED" in line), None)
                        result_reason = stderr_lines[build_failed_line_i + 1]
                        result_reason = result_reason[result_reason.find(' '):]
                        test_result = "ERROR"
                    else:
                        test_result = "FAIL" # test fail
                        result_reason = self.run_bash("get_test_error", project, bug_id).stdout

            if self.validate_patch_cache_folder is not None:
                with open(cache_file_path, "w") as file:
                    json.dump({'patch': proposed_patch, 'test_result': test_result, 'result_reason': result_reason, 'patch_diff': patch_diff}, file,  indent=4, sort_keys=True)
        
        logging.info(f"Test result for patch with the hash {patch_hash} is: {test_result}. The reason for this result is: {result_reason}")
        return test_result, result_reason, patch_diff
    
    def run_bash(self, function, project, bug_id, extra_arg1=None, extra_arg2=None):
        work_dir = f"{self.tmp_dir}/{project}-{bug_id}"
        if sys.platform.startswith('win'):
            command = ['wsl', 'bash', f'{self.shell_script_folder}/{self.name}.sh', function, f"{project}", f"{bug_id}", f"{work_dir}", f"{self.java_home}", f"{self.d4j_path}", f"{extra_arg1}", f"{extra_arg2}"]
        else:
            command = ['bash', f'/{self.shell_script_folder}/{self.name}.sh', function, f"{project}",
                       f"{bug_id}", f"{work_dir}", f"{self.java_home}", f"{self.d4j_path}", f"{extra_arg1}",
                       f"{extra_arg2}"]
        result = run(command, stdout=PIPE, stderr=PIPE, universal_newlines=True, encoding='utf8', errors='replace')
        if len(result.stdout) > 0:
            if result.stdout[-1] == "\n":
                result.stdout = result.stdout[:-1]
        return result

    @staticmethod
    def replace_infill(filename):
        target = '>>> [ INFILL ] <<<'
        replacement = '&'

        try:
            with open(filename, 'r+', encoding='utf-8') as f:
                content = f.read()

                if target not in content:
                    return

                new_content, count = content.replace(target, replacement), content.count(target)

                if new_content != content:
                    f.seek(0)
                    f.truncate()
                    f.write(new_content)
                    logging.info(f"{count} >>> [ INFILL ] <<< found, replaced.")

        except FileNotFoundError:
            print(f"Error: File Not Found '{filename}'")
        except PermissionError:
            print(f"Error: Permission Denied '{filename}'")
        except Exception as e:
            print(f"Error: {str(e)}")
