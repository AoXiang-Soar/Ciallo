import logging

import openai

import user_params
from prog_params import ProgParams as prog_params
from src.bug import Bug
from src.llm import LLM
from src.framework import Framework
from src.prompts import Prompts as prompts
from src.utils import get_error_code_trace


class BaseLLM(object):
    def __init__(self, llm: LLM, framework: Framework):
        self.name = "BaseLLM"
        self.chatgpt = llm
        self.framework = framework

    def repair(self, bug: Bug, mode: str, sample_per_try=1, max_tries=1):
        #assert (mode in ["SL", "SH", "SF"] or self.framework.name == 'humanevaljava')
        if mode.find(' ') != -1:
            mode = mode.split(' ')[0]

        plausible_patches = []
        plausible_patch_diffs = []
        first_plausible_patch_try = 0
        current_conversation_length = 0
        current_tries = 0
        total_cost = 0
        err_tf = 0
        err_ce = 0
        prefix = f"{self.framework.name}_{bug.project}_{bug.bug_id}"

        tmp_dir = user_params.UserParams.D4J_TMP_DIR if self.framework.name == 'defects4j' else user_params.UserParams.HEJ_TMP_DIR
        project_dir = f"{tmp_dir}/{bug.project}-{bug.bug_id}"
        failing_tests_path = f"{project_dir}/failing_tests" if self.framework.name == 'defects4j' \
            else f"{project_dir}/target/surefire-reports/humaneval.TEST_{bug.bug_id}.txt"

        self.framework.run_bash("checkout_bug", bug.project, bug.bug_id)
        self.framework.run_bash("compile_and_run_tests", bug.project, bug.bug_id)
        src_path = self.framework.run_bash("get_source_code_file_path", bug.project, bug.bug_id).stdout
        error_trace = get_error_code_trace(failing_tests_path, src_path)

        while (current_tries < max_tries and len(plausible_patches) == 0):
            prompt = prompts.base_llm_prompt(bug=bug, mode=mode, error_trace=error_trace)

            current_tries += 1
            current_conversation_length += 1

            try:
                response, cost, _ = self.chatgpt.call(prompt, num_of_samples=sample_per_try, prefix=f"{prefix}_R{current_tries}")
                cost += _
                response = response[0]
            except openai.OpenAIError as e:
                logging.info(e)
                err_ce += 1 # Count token exceeded limit as error
                total_cost += prog_params.model_token_limit # Exceeded Token limit
                continue

            total_cost += cost

            patch = self.extract_patch_from_response(response)
            logging.debug(f"Validating response of {bug.project}-{bug.bug_id} ({mode})")
            test_result, result_reason, patch_diff = self.framework.validate_patch(bug=bug, proposed_patch=patch, mode=mode)

            if test_result == "PASS":
                plausible_patches.append(patch)
                plausible_patch_diffs.append(patch_diff)
                first_plausible_patch_try = current_tries

            if test_result == "FAIL":
                err_tf += 1
            elif test_result == "ERROR":
                err_ce += 1
                
            prompt.append({"role": "assistant", "content": f"""{response}"""})
        
        return plausible_patches, plausible_patch_diffs, total_cost, first_plausible_patch_try, current_conversation_length, current_tries, err_tf, err_ce, current_tries

    @staticmethod
    def extract_patch_from_response(response):

        if "```java" in response:
            patch = response[response.find("```java")+len("```java")+1:]
            patch = patch[:patch.find("\n```")]
        else:
            patch = response

        return patch
    