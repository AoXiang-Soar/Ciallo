import os.path

import openai

import user_params
from prog_params import ProgParams as prog_params
from src.bug import Bug
from src.llm import LLM
from src.framework import Framework
from src.get_test_info import extract_failed_tests
from src.prompts import Prompts
from src.proposed_patches import ProposedPatches
from src.utils import extract_patches_from_response


class Ciallo(object):

    def __init__(self, llm: LLM, framework: Framework):
        self.name = "Ciallo"
        self.chatgpt = llm
        self.framework = framework

    def repair(self, bug: Bug, max_fpps_try_per_mode=1, max_mpps_try_per_mode=1, prompt_token_limit=1500, total_token_limit_target=3000,
               max_sample_count=1, similarity_threshold=0.5, max_rounds=1,
               ask_for_bug_description=False, max_patch_limit=15):
        # Initialize
        first_mode = list(bug.bug_type.split())[0]
        if first_mode == "BF":
            modes = ["BF"]
        elif first_mode == "SF":
            modes = ["SF"]
        else:
            modes = [first_mode, "SF"]
        prefix = f"{self.framework.name}_no_understanding_{bug.project}_{bug.bug_id}"
        total_call_tries, total_cost, test_error_count = 0, 0, 0
        first_plausible_patch_try = None
        plausible_patches, plausible_patch_diffs = [], []
        test_failure_count, test_error_count, total_length = 0, 0, 0
        max_mpps_try_per_mode = max_mpps_try_per_mode if not prog_params.stop_on_first_plausible_patch else 0

        tmp_dir = user_params.UserParams.D4J_TMP_DIR \
            if self.framework.name == 'defects4j' else user_params.UserParams.HEJ_TMP_DIR
        project_dir = f"{tmp_dir}/{bug.project}-{bug.bug_id}"
        failing_tests_path = f"{project_dir}/failing_tests" if self.framework.name == 'defects4j' \
            else f"{project_dir}/target/surefire-reports/humaneval.TEST_{bug.bug_id}.txt"

        self.framework.run_bash("checkout_bug", bug.project, bug.bug_id)

        self.framework.run_bash("compile_and_run_tests", bug.project, bug.bug_id)
        failing_tests = extract_failed_tests(failing_tests_path)
        src_path = self.framework.run_bash("get_source_code_file_path", bug.project, bug.bug_id).stdout

        exist_patch = set()
        for round in range(1, max_rounds + 1):
            proposed_patches = ProposedPatches()
            for mode in modes:
                # Build direction prompt
                try:
                    direction_prompt = Prompts.directions_without_understanding_prompt(bug=bug, mode=mode, failing_tests_path=failing_tests_path, src_path=src_path)
                except FileNotFoundError:
                    self.framework.run_bash("checkout_bug", bug.project, bug.bug_id)
                    self.framework.run_bash("compile_and_run_tests", bug.project, bug.bug_id)
                    direction_prompt = Prompts.directions_without_understanding_prompt(bug=bug, mode=mode, failing_tests_path=failing_tests_path, src_path=src_path)
                responses, cost, _ = self.chatgpt.call(direction_prompt, num_of_samples=1, prefix=f"{prefix}_R{round}_{total_call_tries}_Direction")
                cost += _
                directions = responses[-1]
                total_cost += cost

                directions = Prompts.extract_directions(directions)

                is_first_ongoing = True
                # {FirstPlausiblePatchGeneration, PatchMultiplication}
                for run_condition, call_try_limit, construct_prompt_function in [(False, max_fpps_try_per_mode, Prompts.construct_ciallo_fpps_prompt),
                                                                                 (True, max_mpps_try_per_mode, Prompts.construct_ciallo_mpps_prompt)]:
                    call_tries = 0
                    history_proposed_patches = []
                    used_plausible_patches, mul_time = [], 0
                    present_patches = ProposedPatches()

                    plausible_count_last = 0
                    while call_tries < call_try_limit and proposed_patches.contains_plausible_patch(mode) == run_condition:
                        call_tries += 1
                        responses = []
                        try:
                            # FirstPlausiblePatchGeneration and λ_current = 1
                            if not run_condition and call_tries == 1:
                                i=1
                                for d in directions:
                                    prompt = Prompts.initial_tries_without_understanding_prompt(bug=bug, mode=mode, directions_id=i,
                                                                          directions=d, src_path=src_path, should_use_global_info=False)
                                    response, cost, _ = self.chatgpt.call(prompt, num_of_samples=1, prefix=f"{prefix}_R{round}_{total_call_tries}_init_{i}")
                                    cost += _
                                    if not response[-1] in responses:
                                        responses.append(response[-1])
                                    total_cost += cost
                                    total_call_tries += 1
                                    i+=1
                            # FirstPlausiblePatchGeneration and λ_current != 1
                            elif not run_condition and present_patches.length(mode=mode) != 0:
                                prompt, num_of_samples = construct_prompt_function(bug=bug, mode=mode, proposed_patches=present_patches,
                                                                                    n_shot_bugs=None, prompt_token_limit=prompt_token_limit,
                                                                                    total_token_limit_target=total_token_limit_target,
                                                                                    ask_for_bug_description=ask_for_bug_description,
                                                                                    src_path=src_path, history=history_proposed_patches)
                                prompt, history_proposed_patches = prompt
                                for p in prompt:
                                    response, cost, _ = self.chatgpt.call(p, num_of_samples=max(1, min(max_sample_count, num_of_samples)),
                                                                        prefix=f"{prefix}_R{round}_{total_call_tries}_ongoing")
                                    if not response[-1] in responses:
                                        responses.append(response[-1])
                                    cost += _
                                    total_cost += cost
                                    total_call_tries += 1
                            # PatchMultiplication
                            elif run_condition and proposed_patches.length(mode=mode) != 0:
                                mul_time += 1
                                plausible = proposed_patches.get_plausible_patches()
                                if plausible_count_last == len(plausible):
                                    remove_count=max_patch_limit-len(plausible)
                                    if len(used_plausible_patches) >= remove_count:
                                        used_plausible_patches = used_plausible_patches[remove_count:]
                                    else:
                                        used_plausible_patches = []
                                plausible_count_last = len(plausible)
                                for pp in plausible:
                                    if len(plausible) >= max_patch_limit or mul_time > max_mpps_try_per_mode:
                                        break
                                    if pp in used_plausible_patches:
                                        continue
                                    used_plausible_patches.append(pp)
                                    prompt, num_of_samples = construct_prompt_function(bug=bug, mode=mode, proposed_patches=ProposedPatches([pp]),
                                                                                       n_shot_bugs=None, prompt_token_limit=prompt_token_limit,
                                                                                       total_token_limit_target=total_token_limit_target,
                                                                                       ask_for_bug_description=ask_for_bug_description,
                                                                                       src_path=src_path, history=history_proposed_patches)
                                    response, cost, _ = self.chatgpt.call(prompt, num_of_samples=1, prefix=f"{prefix}_R{round}_{total_call_tries}_mul")
                                    if not response[-1] in responses:
                                        responses.append(response[-1])
                                    cost += _
                                    total_cost += cost
                                    total_call_tries += 1
                        except openai.OpenAIError as e:
                            total_cost += prog_params.model_token_limit
                            continue
                        # Validate
                        for res in responses:
                            patches = extract_patches_from_response(bug=bug, response=res, response_mode=mode, similarity_threshold=similarity_threshold)
                            for patch, patch_mode in patches:
                                mark = False
                                for ep in exist_patch:
                                    if patch in ep:
                                        mark = True
                                if mark:
                                    continue

                                exist_patch.add(patch)
                                test_result, result_reason, patch_diff = self.framework.validate_patch(bug=bug, proposed_patch=patch, mode=patch_mode)
                                # Patch Sieve
                                if is_first_ongoing or (os.path.exists(failing_tests_path) and (extract_failed_tests(failing_tests_path) & failing_tests) < failing_tests):
                                    proposed_patches.add(response=res, test_result=test_result, result_reason=result_reason, mode=patch_mode,
                                                    patch=patch, patch_diff=patch_diff)
                                    present_patches.add(response=res, test_result=test_result, result_reason=result_reason, mode=patch_mode,
                                                    patch=patch, patch_diff=patch_diff)
                                if first_plausible_patch_try is None and test_result == 'PASS':
                                    first_plausible_patch_try = total_call_tries
                                if test_result == 'ERROR':
                                    test_error_count += 1
                        if is_first_ongoing:
                            is_first_ongoing = False
                if proposed_patches.contains_plausible_patch(mode=mode):
                    break

            plausible_patches, plausible_patch_diffs = proposed_patches.get_plausible_patches(), proposed_patches.get_plausible_patch_diffs()
            test_failure_count += proposed_patches.get_test_failure_count()
            total_length += proposed_patches.total_length() + test_failure_count
            if proposed_patches.contains_plausible_patch():
                break
        
        return (plausible_patches, plausible_patch_diffs, total_cost,
                first_plausible_patch_try, None, total_call_tries, test_failure_count, test_error_count, total_length)
