import csv
import logging
import os
from pathlib import Path

from prog_params import ProgParams as prog_params
from src.framework import Framework
from src.utils import get_token_count


class Analysis:

    def __init__(self, apr, framework: Framework):
        self.apr = apr
        self.framework = framework

        self.plausible_patches_folder = Path(__file__).parent.parent / 'output' / f'{framework.name}_{apr.name}' / 'plausible_patches'

    def run(self, list_of_bugs_to_fix):
        logging.basicConfig(level=prog_params.logging_level, format='%(funcName)s :: %(levelname)s :: %(message)s')

        for project, ids in list_of_bugs_to_fix:

            summary_file_path = Path(__file__).parent.parent / 'output' / f'{self.framework.name}_{self.apr.name}' / f'{project}_summary.csv'

            fieldnames = self._get_fieldnames()
            if not summary_file_path.exists():
                dir_path = Path(__file__).parent.parent / 'output' / f'{self.framework.name}_{self.apr.name}'
                if not dir_path.exists():
                    os.makedirs(dir_path)
                with open(summary_file_path, 'w', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()

            for bug_id in ids:
                logging.info(f" ---------- Reproducing {project}-{bug_id} ----------")
                bug = self.framework.get_bug_details(project, bug_id)
                logging.info(f"Bug details fetched. Bug type: {bug.bug_type}")

                row = {key: "" for key in fieldnames}
                row['framework'] = f"{self.framework.name}"
                row['project'] = project
                row['bug_id'] = bug_id
                row['bug_type'] = bug.bug_type
                if self.apr.name.lower() == "capr":
                    row['max_conv_length'] = prog_params.capr_max_conv_length

                if bug.bug_type not in ["OT", "BF"] or (bug.bug_type == "BF"
                        and (self.apr.name.lower() == "ciallo" or self.framework.name.lower() == "humanevaljava")):
                    modes = list(bug.bug_type.split()) if self.apr.name.lower() in ["capr"] else [bug.bug_type]

                    for mode in modes:
                        logging.info(f" --- Started repairing {project}-{bug_id} ({mode}) --- ")

                        if self.apr.name.lower() == "basellm":
                            if bug.bug_type == "BF" and self.framework.name.lower() == "humanevaljava":
                                self.framework.run_bash("checkout_bug", bug.project, bug.bug_id)
                                src_path = self.framework.run_bash("get_source_code_file_path", bug.project, bug.bug_id).stdout
                                with open(src_path, 'r') as f:
                                    bug.code = f.read()
                            max_tries = prog_params.basellm_max_rounds
                            repair_results = self.apr.repair(bug=bug, mode=mode, max_tries=max_tries)
                        elif self.apr.name.lower() == "ciallo":
                            if bug.bug_type == "BF":
                                if bug.project == 'Lang' and str(bug.bug_id) == '62':
                                    logging.info(f" --- Skipping {project}-{bug_id}, out of limited tokens.")
                                    row['comment'] += "Out of limited tokens. "
                                    break # Lang-62 not utf8 char
                                self.framework.run_bash("checkout_bug", bug.project, bug.bug_id)
                                src_path = self.framework.run_bash("get_source_code_file_path", bug.project, bug.bug_id).stdout
                                with open(src_path, 'r') as f:
                                    bug.code = f.read()
                            if get_token_count(bug.code) > prog_params.ciallo_bf_token_limit:
                                logging.info(f" --- Skipping {project}-{bug_id}, out of limited tokens. ({get_token_count(bug.code)} > {prog_params.ciallo_bf_token_limit}) --- ")
                                row['comment'] += "Out of limited tokens. "
                                break
                            repair_results = self.apr.repair(bug=bug,
                                                             max_fpps_try_per_mode=prog_params.ciallo_max_fpps_try_per_mode,
                                                             max_mpps_try_per_mode=prog_params.ciallo_max_mpps_try_per_mode,
                                                             prompt_token_limit=prog_params.ciallo_prompt_token_limit,
                                                             total_token_limit_target=prog_params.ciallo_total_token_limit_target,
                                                             max_sample_count=prog_params.ciallo_max_sample_count,
                                                             similarity_threshold=prog_params.ciallo_similarity_threshold,
                                                             max_rounds=prog_params.ciallo_max_rounds,
                                                             max_patch_limit=prog_params.ciallo_max_patch_limit)

                        plausible_patches, plausible_patch_diffs, repair_cost, first_plausible_patch_try, first_plausible_patch_conv_len, used_tries, err_tf, err_ce, tpc = repair_results

                        row['ppc'] = str(len(plausible_patches))
                        row['rc'] = repair_cost
                        row['errtf'] = err_tf
                        row['errce'] = err_ce
                        row['tpc'] = tpc
                        if len(plausible_patches) > 0:
                            row['fppt'] = first_plausible_patch_try
                            if self.apr.name.lower() == "capr":
                                row['fppcl'] = first_plausible_patch_conv_len
                            logging.info(f"Finished repair attempt of {project}-{bug_id} ({mode}), found {len(plausible_patches)} plausible patches. Used {used_tries} tries totalling {repair_cost} tokens.")
                        else:
                            logging.info(f"Finished repair attempt of {project}-{bug_id} ({mode}), no plausible patches found. Used {used_tries} tries totalling {repair_cost} tokens.")

                        for i, plausible_patch_diff in enumerate(plausible_patch_diffs):
                            if not os.path.isdir(f'{self.plausible_patches_folder}'):
                                os.mkdir(f'{self.plausible_patches_folder}')
                            with open(f'{self.plausible_patches_folder}/{project}_{bug_id}_{i}.diff', 'w+') as f:
                                f.writelines(plausible_patch_diff)

                else:
                    logging.info(f" --- Skipping {project}-{bug_id}, not SL, SH or SF bug. --- ")
                    row['comment'] += "Not SL, SH or SF bug. "

                with open(summary_file_path, 'a', newline='') as csvfile:
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writerow(row)

    def _get_fieldnames(self):
        if self.apr.name.lower() == "ciallo":
            return ['framework', 'project', 'bug_id', 'bug_type',
                    'ppc', 'rc', 'fppt', 'errtf', 'errce', 'tpc',
                    'comment']
        elif self.apr.name.lower() == "basellm":
            return ['framework', 'project', 'bug_id', 'bug_type',
                    'ppc', 'rc', 'fppt', 'errtf', 'errce', 'tpc',
                    'comment']
