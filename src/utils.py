import copy
import json
import os
import random
import re

from difflib import SequenceMatcher
from itertools import combinations

import deepseek_v3_tokenizer.deepseek_tokenizer
import tiktoken
from src.proposed_patches import ProposedPatches
from src.bug import Bug
from prog_params import ProgParams as prog_params


def extract_patches_from_response(bug: Bug, response, response_mode, similarity_threshold):

    patches = []

    if "```java" in response:

        code_blocks_in_response = response.count("```java")
        for _ in range(code_blocks_in_response):
            patch_block = response[response.find("```java")+len("```java")+1:]
            patch_block = patch_block[:patch_block.find("\n```")]
            patches.append((patch_block, response_mode))

            if response_mode == "BF":
                return patches
            
            patch = synthetize_and_extract_patch(patch_block=patch_block, masked_code=bug.masked_code, buggy_lines=bug.buggy_lines)
            patches.append((patch, response_mode)) if patch not in [p[0] for p in patches] else None

            if response_mode != "SF":
                buggy_function_and_patch_similarity = similarity(bug.code, patch_block)
                if (buggy_function_and_patch_similarity > similarity_threshold):
                    patches.append((patch_block, "SF"))

            response = response[response.find("\n```")+len("\n```")+1:]

    else:
        patches.append((response, response_mode))

    return patches


def synthetize_and_extract_patch(patch_block, masked_code, buggy_lines):
    masked_code_lines = masked_code.split('\n')
    
    infill_line_count = 0
    for i in range(len(masked_code_lines)):
        if 'INFILL' in masked_code_lines[i]:
            infill_line_count = i
            break

    patch_block_num_of_lines = len(patch_block.split('\n'))

    pre_infill_lines = masked_code_lines[max(0,infill_line_count-patch_block_num_of_lines):infill_line_count]
    post_infill_lines = masked_code_lines[infill_line_count+1:min(infill_line_count+patch_block_num_of_lines+1, len(masked_code_lines))]

    buggy_code_block_lines = pre_infill_lines + [buggy_lines] + post_infill_lines
    buggy_code_block = '\n'.join(buggy_code_block_lines)

    synthetized_code_lines = None
    synthesized_code_similarity = 0
    r = min((patch_block_num_of_lines - 1) * 2 + 1, len(buggy_code_block_lines))

    for synthetized_candidate_lines in [c for c in combinations(pre_infill_lines + [patch_block] + post_infill_lines, r) if patch_block in c]:
        synthesized_candidate_code = '\n'.join(synthetized_candidate_lines)
        candidate_similarity = similarity(buggy_code_block, synthesized_candidate_code)
        if candidate_similarity > synthesized_code_similarity:
            synthesized_code_similarity = candidate_similarity
            synthetized_code_lines = synthetized_candidate_lines

    if synthetized_code_lines is None:
        return patch_block

    patch = '\n'.join(synthetized_code_lines).split('\n')

    for i in range(len(buggy_code_block_lines)):
        if buggy_code_block_lines[i] == patch[0]:
            if len(patch) > 1:
                patch.pop(0)
        else:
            break

    for i in range(len(buggy_code_block_lines)-1, -1, -1):
        if buggy_code_block_lines[i] == patch[-1]:
            if len(patch) > 1:
                patch.pop()
        else:
            break

    for _ in range(len(patch)):
        if patch[0] in buggy_code_block_lines:
            if len(patch) > 0:
                patch.pop(0)
        else:
            break

    for _ in range(len(patch)-1, -1, -1):
        if patch[-1] in buggy_code_block_lines:
            if len(patch) > 0:
                patch.pop()
        else:
            break

    return '\n'.join(patch)


def similarity(a: str, b: str):
    return SequenceMatcher(None, a, b).ratio()


def get_token_count(prompt):
    #enc = deepseek_v3_tokenizer.deepseek_tokenizer.tokenizer
    enc = tiktoken.encoding_for_model(prog_params.gpt4_model[0])

    if isinstance(prompt, list):
        token_count = 0
        for d in prompt:
            token_count += len(enc.encode(d['content']))

        token_count += len(prompt) * 5 + 3 # Special tokens

        return token_count
    
    if isinstance(prompt, str):
        return len(enc.encode(prompt))


def count_num_of_samples(bug:Bug, prompt, proposed_patches: ProposedPatches, mode, total_token_limit_target):
    prompt_token_count = get_token_count(prompt)
    responses = proposed_patches.get_responses(mode)
    if len(responses) > 0:
        average_response_token_count = int(sum([get_token_count(response) for response in responses]) // len(responses))
    else:
        if mode == "SF":
            average_response_token_count = int(get_token_count(bug.code))
        else:
            average_response_token_count = int(get_token_count(bug.buggy_lines) + get_token_count(bug.code) // 10)
    if average_response_token_count < 5:
        average_response_token_count = 100

    return int((total_token_limit_target - prompt_token_count) // average_response_token_count)


def extract_error_context(error_path, file_path, line_range):
    with open(error_path, 'r', encoding='utf-8') as f:
        error_text = f.read()
    target_filename = file_path.replace('\\', '/').split('/')[-1]

    error_blocks = re.split(r'---', error_text.strip())

    selected_block = None
    for block in error_blocks:
        if re.search(rf'.*\({target_filename}:\d+\)$', block, re.MULTILINE):
            selected_block = block
            break

    if not selected_block:
        return []

    matches = []
    for match in selected_block.split('\n'):
        pattern = re.compile(rf'(.*)\({target_filename}:(\d+)\)$')
        m = pattern.match(match)
        if m:
            matches.append(m.group(2))

    relevant_linenos = list(reversed(matches))

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = [line.rstrip('\n') for line in f]
    except FileNotFoundError:
        return []

    count = 0
    result = []
    for lineno in relevant_linenos:
        count += 1
        if count >= 20:
            break
        idx = int(lineno) - 1
        context = []
        for i in range(max(idx - line_range, 0), min(len(lines)-1, idx + line_range + 1)):
            if i == idx:
                context.append(lines[i] + f'\t// HERE IS LINE {lineno}')
                continue
            context.append(lines[i])
        result.append(context)

    return result

def get_error_code_trace(error_path, file_path, line_range=3):
    context = extract_error_context(error_path, file_path, line_range)
    if len(context) == 0:
        return None
    lines = ''
    for con in context:
        ls = '// ...\n'
        for c in con:
            ls += c + '\n'
        lines += ls
    lines += '// ...'
    return lines

def get_random_sample_set(total_d4j, total_hej):
    set_file = prog_params.random_sample_set
    d4j_list = [(x, []) for x, y in prog_params.d4j_list_of_bugs]
    hej_list = [("humanevaljava", [])]
    if os.path.isfile(set_file):
        with open(set_file, 'r', encoding='utf-8') as f:
            d4j_list, hej_list = json.load(f)
    else:
        assert (0 < total_d4j < 486-24) and (0 < total_hej < 163) # No Collections [1-24]
        d4j_set = copy.deepcopy(prog_params.d4j_list_of_bugs)
        hej_set = copy.deepcopy(prog_params.humaneval_list_of_bugs)
        for i in range(total_d4j):
            while True:
                index = random.randint(0, len(d4j_set) - 1)
                name, l1 = d4j_set[index]
                if len(l1) == 0:
                    continue
                sample = l1[random.randint(0, len(l1) - 1)]
                l1.remove(sample)
                with open(f'{prog_params.bug_details_cache_folder}/{name}-{sample}.json', 'r', encoding='utf-8') as f:
                    bug_type = json.load(f)["bug_type"]
                if bug_type in ["BF", "OT"]:
                    continue
                if name == 'Collections' and sample in range(1, 25):
                    continue
                _, l2 = d4j_list[index]
                l2.append(sample)
                break
        for i in range(total_hej):
            name, l1 = hej_set[0]
            sample = l1[random.randint(0, len(l1) - 1)]
            l1.remove(sample)
            _, l2 = hej_list[0]
            l2.append(sample)
        for x,y in d4j_list:
            y.sort()
        for x, y in hej_list:
            y.sort()
        with open(set_file, "w") as f:
            json.dump((d4j_list, hej_list), f, indent=2)
    return d4j_list, hej_list

def find_last_valid_brace(content):
    in_block_comment = False
    in_line_comment = False
    last_brace_pos = -1
    i = 0

    while i < len(content):
        if in_block_comment:
            if content[i] == '*' and i + 1 < len(content) and content[i + 1] == '/':
                in_block_comment = False
                i += 2
            else:
                i += 1

        elif in_line_comment:
            if content[i] == '\n':
                in_line_comment = False
            i += 1

        else:
            if content[i] == '/':
                if i + 1 < len(content):
                    next_char = content[i + 1]
                    if next_char == '*':
                        in_block_comment = True
                        i += 2
                    elif next_char == '/':
                        in_line_comment = True
                        i += 2
                    else:
                        i += 1
                else:
                    i += 1

            elif content[i] == '}':
                last_brace_pos = i
                i += 1

            else:
                i += 1

    return last_brace_pos if last_brace_pos != -1 else None


def insert_method(method_str, java_file_path):
    with open(java_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    brace_pos = find_last_valid_brace(content)
    if brace_pos is None:
        raise ValueError("Valid class closing brace not found")

    # Insert method before the closing curly brace
    new_content = (
            content[:brace_pos].rstrip() +
            '\n' + method_str + '\n' +
            content[brace_pos:].lstrip()
    )

    with open(java_file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

if __name__ == '__main__':
    print(get_token_count('Hello'))