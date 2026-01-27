from src.bug import Bug
from src.proposed_patches import ProposedPatches, ProposedPatch
from src.utils import count_num_of_samples, get_token_count, get_error_code_trace
from src.get_global_information import analyze
import re

class Prompts(object):

    # Ciallo Prompts
    @staticmethod
    def construct_initial_message(bug: Bug, mode: str, n_shot_bugs=None):
        n_shot_examples_text = ""
        if n_shot_bugs:
            for n_shot_bug in n_shot_bugs:
                n_shot_initial_prompt = Prompts.construct_initial_message(bug=n_shot_bug, mode=mode, n_shot_bugs=None)
                if mode == "SL":
                    n_shot_examples_text += f"{n_shot_initial_prompt}\n\nIt can be fixed by these possible line:\n```java\n{n_shot_bug.fixed_lines}\n```\n\n"
                elif mode == "SH":
                    n_shot_examples_text += f"{n_shot_initial_prompt}\n\nIt can be fixed by the following hunk:\n```java\n{n_shot_bug.fixed_lines}\n```\n\n"
                elif mode == "SF":
                    n_shot_examples_text += f"{n_shot_initial_prompt}\n\nIt can be fixed by the following function:\n```java\n{n_shot_bug.fixed_code}\n```\n\n"

        if mode == "SL":
            prompt_header = f"""The following code contains a buggy line that has been removed.\n```java\n{bug.masked_code}\n```
This was the original buggy line which was removed by the infill location:
```java\n{bug.buggy_lines}\n```"""
            prompt_footer = "Please provide the correct line at the infill location."

        elif mode == "SH":
            prompt_header = f"""The following code contains a buggy hunk that has been removed.\n```java\n{bug.masked_code}\n```
This was the original buggy hunk which was removed by the infill location:
```java\n{bug.buggy_lines}\n```"""
            prompt_footer = "Please provide the correct hunk at the infill location."

        elif mode == "SF":
            prompt_header = f"""The following code contains a bug\n```java\n{bug.code}\n```"""
            prompt_footer = "Please provide the correct function."

        initial_prompt_message= f"""{n_shot_examples_text}{prompt_header}
The code fails on this test:\n```\n{bug.test_name}\n```
on this test line:\n```java\n{bug.test_line}\n```
with the following test error:\n```\n{bug.test_error_message}\n```
{prompt_footer}"""

        return initial_prompt_message


    @staticmethod
    def system_message():
        return "You are an automated program repair tool."

    @staticmethod
    def n_shot_example_message(bug: Bug, n_shot_bugs, mode, ask_for_bug_description=False):
        if len(n_shot_bugs) == 0:
            return ""
        n_shot_bug = n_shot_bugs[0]
        
        if mode == "SL":
            bug_fix = f"```java\n{n_shot_bug.fixed_lines}\n```"
        elif mode == "SH":
            bug_fix = f"```java\n{n_shot_bug.fixed_lines}\n```"
        elif mode == "SF":
            bug_fix = f"```java\n{n_shot_bug.fixed_code}\n```"
        
        return "\n".join([Prompts.code_introduction_message(bug=n_shot_bug, mode=mode),
                          Prompts.bug_details(bug=n_shot_bug, mode=mode),
                          Prompts.fpps_call_to_action(mode=mode, ask_for_bug_description=ask_for_bug_description),
                          Prompts.solution_message(mode=mode, solution_list=[n_shot_bug]),
                          bug_fix])

    @staticmethod
    def solution_message(mode, solution_list):
        s = "s" if len(solution_list) > 1 else ""
        if mode == "SL":
            solution_message = f"It can be fixed by these possible line{s}:"
        elif mode == "SH":
            solution_message = f"It can be fixed by the following hunk{s}:"
        elif mode == "SF":
            solution_message = f"It can be fixed by the following function{s}:"
        elif mode == "BF":
            solution_message = f"It can be fixed by the following program{s}:"
        return solution_message

    @staticmethod
    def code_introduction_message(bug: Bug, mode):
        if mode == "SL":
            return f"The following code contains a buggy line that has been removed.\n```java\n{bug.masked_code}\n```"
        elif mode == "SH":
            return f"The following code contains a buggy hunk that has been removed.\n```java\n{bug.masked_code}\n```"
        elif mode == "SF":
            return f"The following code contains a bug.\n```java\n{bug.code}\n```"
        elif mode == "BF":
            return f"The following code contains a bug.\n```java\n{bug.code}\n```"

    @staticmethod
    def bug_details(bug: Bug, mode):
        bug_details = "\n".join([
                f"The code fails on this test:\n```\n{bug.test_name}\n```",
                f"on this test line:\n```java\n{bug.test_line}\n```",
                f"with the following test error:\n```\n{bug.test_error_message}\n```"
            ])

        if mode == "SL":
            return "\n".join([f"This was the original buggy line which was removed by the infill location:\n```java\n{bug.buggy_lines}\n```",
                              bug_details])
        elif mode == "SH":
            return "\n".join([f"This was the original buggy hunk which was removed by the infill location:\n```java\n{bug.buggy_lines}\n```",
                              bug_details])
        else:
            return bug_details

    @staticmethod
    def fpps_call_to_action(mode, ask_for_bug_description=False):
        bug_description = "."
        if ask_for_bug_description:
            bug_description = "\n".join([
                " in the following format:",
                "BUG DESCRIPTION:",
                "Explain here what is wrong with the code and how to fix it.",
                "CODE FIX:",
                "```java",
                "The correct code fix goes here.",
                "```"
            ])
        
        if mode == "SL":
            return f"Please provide the correct line at the infill location{bug_description}"
        elif mode == "SH":
            return f"Please provide the correct hunk at the infill location{bug_description}"
        elif mode == "SF":
            return f"Please provide the correct function{bug_description}"
        elif mode == "BF":
            return f"Please provide the correct program{bug_description}"

    @staticmethod
    def mpps_call_to_action(mode):
        if mode == "SL":
            return "Please generate an alternative fix line."
        elif mode == "SH":
            return "Please generate an alternative fix hunk."
        elif mode == "SF":
            return "Please generate an alternative fix function."
        elif mode == "BF":
            return "Please generate an alternative fix program."

    @staticmethod
    def feedback_on_response(bug: Bug, proposed_patch: ProposedPatch):
        if proposed_patch.result_reason == bug.test_error_message:
            return f"The fixed version is still not correct. It still does not fix the original test failure."
        else:
            error_type = "test error" if proposed_patch.test_result == "FAIL" else "compilation error"
            return f"""The fixed version is still not correct. Code has the following {error_type}:\n```\n{proposed_patch.result_reason}\n```"""


    @staticmethod
    def summarize_plausible_patches(plausible_patches, summary_token_limit):
        mode = plausible_patches[0].mode

        included_patches = []
        summary_message = ""

        for plausible_patch in reversed(plausible_patches):

            included_patches.append(plausible_patch)
            listed_plausible_patches = "\n".join([f"""{i+1}. ```java\n{pp.patch}\n```""" for i, pp in enumerate(included_patches)])

            summary_message = "\n".join([Prompts.solution_message(mode=mode, solution_list=included_patches), listed_plausible_patches])

            if get_token_count(summary_message) > summary_token_limit:
                break
            
        return summary_message


    @staticmethod
    def initial_fpps_prompt(bug: Bug, mode, n_shot_bugs, ask_for_bug_description=False):
        system_message = Prompts.system_message()

        user_message = "\n".join([Prompts.n_shot_example_message(bug=bug, n_shot_bugs=n_shot_bugs, mode=mode),
                                  Prompts.code_introduction_message(bug=bug, mode=mode),
                                  Prompts.bug_details(bug=bug, mode=mode),
                                  Prompts.fpps_call_to_action(mode=mode, ask_for_bug_description=ask_for_bug_description)])
            
        return [{"role": "system", "content": system_message}, 
                {"role": "user", "content": user_message}]


    @staticmethod
    def construct_mpps_prompt(bug: Bug, mode, proposed_patches: ProposedPatches, n_shot_bugs, prompt_token_limit, total_token_limit_target, ask_for_bug_description=False):
        prompt = Prompts.ongoing_mpps_prompt(bug=bug, mode=mode, proposed_patches=proposed_patches, prompt_token_limit=prompt_token_limit)

        num_of_samples = count_num_of_samples(bug=bug, prompt=prompt, proposed_patches=proposed_patches, mode=mode, total_token_limit_target=total_token_limit_target)

        return prompt, num_of_samples

    @staticmethod
    def ongoing_mpps_prompt(bug: Bug, mode, proposed_patches: ProposedPatches, prompt_token_limit):
        
        user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode), Prompts.bug_details(bug=bug, mode=mode), Prompts.mpps_call_to_action(mode=mode)])
        summary_token_limit = prompt_token_limit - get_token_count(user_message)

        plausible_patch_summary = Prompts.summarize_plausible_patches(plausible_patches=proposed_patches.get_plausible_patches(mode), summary_token_limit=summary_token_limit)
        
        user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                            Prompts.bug_details(bug=bug, mode=mode), 
                            plausible_patch_summary, 
                            Prompts.mpps_call_to_action(mode=mode)])

        return [{"role": "system", "content": "You are an automated program repair tool."},
                {"role": "user", "content": f"{user_message}"}]


    @staticmethod
    def grouping_test_cases_prompt(bug: Bug, mode):
        system_message = Prompts.system_message()
        user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                  f"Here is the complete test code:```java\n{bug.test_function}\n```",
                                  f"Please identify which test cases are used to test boundary conditions and group the test cases accordingly."])

        return [{"role": "system", "content": system_message},
                {"role": "user", "content": user_message}]

    @staticmethod
    def directions_prompt(bug: Bug, mode, assistant_response_message, src_path, failing_tests_path):
        system_message = Prompts.system_message()
        error_trace = get_error_code_trace(failing_tests_path, src_path)
        user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                  f"Here is the complete test code:```java\n{bug.test_function}\n```",
                                  f"{"Here is the corresponding code in the call stack of the error message:\n"+error_trace if error_trace and error_trace != '' and bug.bug_type in ['SF', 'BF'] else ""}",
                                  f"Please identify which test cases are used to test boundary conditions and group the test cases accordingly."])
        user_feedback_message = "\n".join([f"Now you understand the scenarios these test cases are targeting.",
                                  Prompts.bug_details(bug=bug, mode=mode),
                                  Prompts.directions_to_action()])
        return [{"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_response_message},
                {"role": "user", "content": user_feedback_message}]

    @staticmethod
    def directions_to_action():
        return f'''Now you understand the root cause of the bug. If you were to fix this buggy code now, from which directions might you approach the repair? Please list all possible directions in numbered order.
Here is an example output format. Please respond in the same format (each direction starts with a number and is entirely enclosed in **):  
1. **Add an if statement to check the loop exit condition and avoid an infinite loop**  
2. **Change the condition in the while loop from true to a valid continuation condition**'''

    @staticmethod
    def get_requirement(mode):
        requirement = ''
        if mode == 'SL':
            requirement = '''Your response should only contain a single line of code that needs to replace >>> [ INFILL ] <<<, for example:
        For a buggy code (The intention of the code is to print the value of count for count times.):
        ```java
        void printByCount(int count) {
            >>> [ INFILL ] <<<
                System.out.println(count);
            }
        }
        ```
        The part with the buggy code >>> [ INFILL ] <<< is
        ```java
            for(int i = 0; i <= count; i++) {
        ```
        Your out put format should like:
        ```java
            for(int i = 0; i < count; i++) {
        ```'''
        elif mode == 'SH':
            requirement = '''Your response should only contain a single hunk of code that needs to replace >>> [ INFILL ] <<<, for example:
        For a buggy code (The intention of the code is to print the value of count for count times.):
        ```java
        void printByCount(int count) {
            >>> [ INFILL ] <<<
                System.out.println(count);
            }
        }
        ```
        The part with the buggy code >>> [ INFILL ] <<< is
        ```java
            while (count != 0) {
                count--;
        ```
        Your out put format should like:
        ```java
            for(int i = 0; i < count; i++) {
        ```'''
        elif mode == 'SF':
            requirement = '''Your response should only contain a complete function, for example:
        For a buggy code (The intention of the code is to print the value of count for count times.):
        ```java
        void printByCount(int count) {
            while (count != 0) {
                count--;
                System.out.println(count);
            }
        }
        ```
        Your out put format should like:
        ```java
        void printByCount(int count) {
            while (count > 0) {
                System.out.println(count);
                count--;
            }
        }
        ```'''
        elif mode == 'BF':
            requirement = '''Your response should only contain a complete program within a single Java file, for example:
        For a buggy code (The intention of the code is to print the value of count for count times.):
        ```java
        package example;

        import java.utils.*;

        public class Example {
            void printByCount(int count) {
                while (count != 0) {
                    count--;
                    System.out.println(count);
                }
            }
        }
        ```
        Your out put format should like:
        ```java
        package example;

        import java.utils.*;

        public class Example {
            void printByCount(int count) {
                while (count > 0) {
                    System.out.println(count);
                    count--;
                }
            }
        }
        ```'''
        return requirement


    @staticmethod
    def initial_tries_prompt(bug: Bug, mode, directions_id, directions, test_case_groups, src_path, should_use_global_info=False):
        prompts = []
        requirement = Prompts.get_requirement(mode)
        system_message = Prompts.system_message()
        user_message_case = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                  f"Here is the complete test code:```java\n{bug.test_function}\n```",
                                  f"Please identify which test cases are used to test boundary conditions and group the test cases accordingly."])
        user_message = "\n".join([f"Now you understand the scenarios these test cases are targeting.",
                                  Prompts.bug_details(bug=bug, mode=mode),
                                  f"{"Here is the global variables and methods, you can use them to help you to repair the buggy code:\n"}{analyze(src_path)}" if should_use_global_info else "",
                                  f'Please follow the format requirements above and perform repairs according to the direction: {directions}. Please be careful not to introduce new variables or functions.',
                                  requirement])
        prompts.append({"role": "system", "content": system_message})
        prompts.append({"role": "user", "content": user_message_case})
        prompts.append({"role": "assistant", "content": test_case_groups})
        prompts.append({"role": "user", "content": user_message})
        return prompts


    @staticmethod
    def construct_ciallo_fpps_prompt(bug: Bug, mode, proposed_patches: ProposedPatches, n_shot_bugs, prompt_token_limit,
                                     total_token_limit_target, src_path, history, ask_for_bug_description=False):

        if proposed_patches.length(mode=mode) == 0:
            prompt = Prompts.initial_fpps_prompt(bug=bug, mode=mode, n_shot_bugs=n_shot_bugs,
                                                 ask_for_bug_description=ask_for_bug_description)
        else:
            prompt = Prompts.ongoing_prompt(bug=bug, mode=mode, proposed_patches=proposed_patches,
                                                 prompt_token_limit=prompt_token_limit,
                                                 ask_for_bug_description=ask_for_bug_description, src_path=src_path, history=history)

        return prompt, 1

    @staticmethod
    def construct_ciallo_mpps_prompt(bug: Bug, mode, proposed_patches: ProposedPatches, n_shot_bugs, prompt_token_limit, total_token_limit_target, src_path, history, ask_for_bug_description=False):
        return Prompts.construct_mpps_prompt(bug=bug, mode=mode, prompt_token_limit=prompt_token_limit, proposed_patches=proposed_patches, n_shot_bugs=n_shot_bugs, total_token_limit_target=total_token_limit_target)

    @staticmethod
    def ongoing_prompt(bug: Bug, mode, proposed_patches: ProposedPatches, prompt_token_limit,
                                  src_path, history, ask_for_bug_description=False):
        ordered_proposed_patches = proposed_patches.order(mode=mode)

        system_message = Prompts.system_message()
        prompts = []
        while len(ordered_proposed_patches) > 0:
            last_proposed_patch = ordered_proposed_patches.pop()
            if last_proposed_patch in history:
                continue
            history.append(last_proposed_patch)
            last_assistant_response_message = last_proposed_patch.response
            user_feedback_message = "\n".join([Prompts.feedback_on_response(bug=bug, proposed_patch=last_proposed_patch),
                                               f"{"Here is the global variables and methods, you can use them to help you to repair the buggy code:\n"}{analyze(src_path)}"
                                                    if last_proposed_patch.result_reason == 'error: cannot find symbol' and mode != "BF" else '',
                                               Prompts.fpps_call_to_action(mode=mode, ask_for_bug_description=ask_for_bug_description)])

            user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                      Prompts.bug_details(bug=bug, mode=mode),
                                      Prompts.fpps_call_to_action(mode=mode, ask_for_bug_description=ask_for_bug_description)])
            prompts.append([{"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": last_assistant_response_message},
                {"role": "user", "content": user_feedback_message}])
        return (prompts, proposed_patches.order(mode=mode))


    @staticmethod
    def extract_directions(text):
        pattern = re.compile(r'^\d+\.\s*\*\*(.*?)\*\*(.*?)(-(.+))?$')

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        suggestions = []

        for line in lines:
            match = pattern.match(line)
            if match:
                core_content = f"**{match.group(1)}**{' ' + match.group(3) if match.group(3) else ''}"
                suggestions.append(core_content)

        return suggestions

    # BaseLLM Prompts

    @staticmethod
    def base_llm_prompt(bug: Bug, mode, error_trace):
        system_message = Prompts.system_message()
        user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                  f"Here is the complete test code:```java\n{bug.test_function}\n```",
                                  f"{"Here is the corresponding code in the call stack of the error message:\n"+error_trace if error_trace and error_trace != '' and bug.bug_type in ['SF', 'BF'] else ""}",
                                  Prompts.bug_details(bug=bug, mode=mode),
                                  Prompts.get_requirement(mode=mode),
                                  Prompts.fpps_call_to_action(mode=mode)])

        return [{"role": "system", "content": system_message},
                {"role": "user", "content": user_message}]

    # Ablation Experiment

    @staticmethod
    def directions_without_understanding_prompt(bug: Bug, mode, src_path, failing_tests_path):
        system_message = Prompts.system_message()
        error_trace = get_error_code_trace(failing_tests_path, src_path)
        user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                  f"Here is the complete test code:```java\n{bug.test_function}\n```",
                                  f"{"Here is the corresponding code in the call stack of the error message:\n"+error_trace if error_trace and error_trace != '' and bug.bug_type in ['SF', 'BF'] else ""}",
                                  Prompts.bug_details(bug=bug, mode=mode),
                                  Prompts.directions_to_action()])
        return [{"role": "system", "content": system_message},
                {"role": "user", "content": user_message}]

    @staticmethod
    def initial_tries_without_understanding_prompt(bug: Bug, mode, directions_id, directions, src_path, should_use_global_info=False):
        prompts = []
        requirement = Prompts.get_requirement(mode)
        system_message = Prompts.system_message()
        user_message = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                  f"Here is the complete test code:```java\n{bug.test_function}\n```",
                                  Prompts.bug_details(bug=bug, mode=mode),
                                  f"{"Here is the global variables and methods, you can use them to help you to repair the buggy code:\n"}{analyze(src_path)}" if should_use_global_info else "",
                                  f'Please follow the format requirements above and perform repairs according to the direction: {directions}. Please be careful not to introduce new variables or functions.',
                                  requirement])
        prompts.append({"role": "system", "content": system_message})
        prompts.append({"role": "user", "content": user_message})
        return prompts

    @staticmethod
    def initial_tries_without_direction_prompt(bug: Bug, mode, test_case_groups, src_path, should_use_global_info=False):
        prompts = []
        requirement = Prompts.get_requirement(mode)
        system_message = Prompts.system_message()
        user_message_case = "\n".join([Prompts.code_introduction_message(bug=bug, mode=mode),
                                  f"Here is the complete test code:```java\n{bug.test_function}\n```",
                                  f"Please identify which test cases are used to test boundary conditions and group the test cases accordingly."])
        user_message = "\n".join([f"Now you understand the scenarios these test cases are targeting.",
                                  Prompts.bug_details(bug=bug, mode=mode),
                                  f"{"Here is the global variables and methods, you can use them to help you to repair the buggy code:\n"}{analyze(src_path)}" if should_use_global_info else "",
                                  f'Please follow the format requirements above and perform repairs. Please be careful not to introduce new variables or functions.',
                                  requirement])
        prompts.append({"role": "system", "content": system_message})
        prompts.append({"role": "user", "content": user_message_case})
        prompts.append({"role": "assistant", "content": test_case_groups})
        prompts.append({"role": "user", "content": user_message})
        return prompts