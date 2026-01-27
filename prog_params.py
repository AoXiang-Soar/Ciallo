import logging
from pathlib import Path

class ProgParams:

    ### Framework related
    program_dir = '/app'
    shell_script_folder = program_dir +'/' "frameworks"
    validate_patch_cache_folder=program_dir +'/' 'cache' '/' 'validate_patch_cache'
    bug_details_cache_folder=program_dir +'/' 'cache' '/' 'bug_details_cache'
    n_shot_cache_folder=program_dir +'/' 'cache' '/' 'n_shot_cache'
    project_cache_folder = program_dir + '/' 'cache' '/' 'projects'
    random_sample_set = program_dir + '/random_sample_set.json'

    # Defects4J related
    d4j_list_of_bugs = [("Chart", [i for i in range(1, 27)]),
                        ("Cli", [i for i in range(1, 41) if i not in [6]]),
                        ("Closure", [i for i in range(1, 177) if i not in [63, 93]]),
                        ("Codec", [i for i in range(1, 19)]),
                        ("Collections", [i for i in range(1, 29)]),
                        ("Compress", [i for i in range(1, 48)]),
                        ("Csv", [i for i in range(1, 17)]),
                        ("Gson", [i for i in range(1, 19)]),
                        ("JacksonCore", [i for i in range(1, 27)]),
                        ("JacksonDatabind", [i for i in range(1, 113) if i not in [65, 89]]),
                        ("JacksonXml", [i for i in range(1, 7)]),
                        ("Jsoup", [i for i in range(1, 94)]),
                        ("JxPath", [i for i in range(1, 23)]),
                        ("Lang", [i for i in range(1, 66) if i not in [2, 18, 25, 48]]),
                        ("Math", [i for i in range(1, 107)]),
                        ("Mockito", [i for i in range(1, 39)]),
                        ("Time", [i for i in range(1, 28) if i not in [21]])]
    d4j_single_file_bugs = {'Chart': [2, 15, 16, 19, 21, 22, 25],
                            'Cli': [1, 7, 10, 18, 22, 23, 33, 39],
                            'Closure': [3, 6, 8, 9, 16, 17, 26, 27, 28, 41, 43, 45, 46, 49, 51, 60, 64, 68, 74, 75, 76, 80, 84, 85, 98, 100, 108, 112, 127, 139, 140, 151, 156, 166, 170, 172, 175],
                            'Codec': [11, 12, 16],
                            'Collections': [2, 4, 7, 8, 10, 16, 17, 21, 23, 24, 25, 26, 27, 28],
                            'Compress': [2, 3, 6, 9, 20, 22, 34, 39, 43, 47],
                            'Csv': [7, 8, 12, 16],
                            'Gson': [1, 2, 3, 7, 8, 14],
                            'JacksonCore': [10, 13, 14, 16, 17, 22],
                            'JacksonDatabind': [2, 3, 4, 9, 14, 18, 20, 21, 23, 26, 29, 31, 32, 33, 36, 40, 41, 43, 44, 50, 55, 56, 60, 66, 68, 69, 71, 72, 75, 77, 78, 80, 81, 84, 86, 87, 93, 94, 98, 104, 105, 106, 108, 110],
                            'JacksonXml': [2, 6],
                            'Jsoup': [4, 7, 8, 9, 11, 12, 16, 17, 18, 29, 30, 36, 44, 66, 67, 69, 73, 74, 78, 79, 81],
                            'JxPath': [2, 3, 14, 15, 18, 20],
                            'Lang': [4, 7, 8, 13, 15, 20, 23, 29, 30, 32, 34, 35, 36, 41, 46, 47, 50, 56, 60, 62, 63, 64],
                            'Math': [8, 12, 15, 16, 18, 29, 35, 36, 37, 44, 46, 47, 49, 54, 61, 62, 65, 66, 67, 68, 76, 81, 83, 90, 92, 93, 99, 100, 104],
                            'Mockito': [2, 3, 4, 6, 9, 10, 11, 15, 21, 23, 25, 31, 32, 35, 36, 37],
                            'Time': [3, 6, 9, 10, 11, 13]}

    humaneval_list_of_bugs = [("humanevaljava",
                            ["ADD",
                            "ADD_ELEMENTS",
                            "ADD_EVEN_AT_ODD",
                            "ALL_PREFIXES",
                            "ANTI_SHUFFLE",
                            "ANY_INT",
                            "BELOW_THRESHOLD",
                            "BELOW_ZERO",
                            "BF",
                            "BY_LENGTH",
                            "CAN_ARRANGE",
                            "CAR_RACE_COLLISION",
                            "CHANGE_BASE",
                            "CHECK_DICT_CASE",
                            "CHECK_IF_LAST_CHAR_IS_A_LETTER",
                            "CHOOSE_NUM",
                            "CIRCULAR_SHIFT",
                            "CLOSEST_INTEGER",
                            "COMMON",
                            "COMPARE",
                            "COMPARE_ONE",
                            "CONCATENATE",
                            "CORRECT_BRACKETING",
                            "COUNT_DISTINCT_CHARACTERS",
                            "COUNT_NUMS",
                            "COUNT_UPPER",
                            "COUNT_UP_TO",
                            "CYCPATTERN_CHECK",
                            "DECIMAL_TO_BINARY",
                            "DECODE_CYCLIC",
                            "DECODE_SHIFT",
                            "DERIVATIVE",
                            "DIGITS",
                            "DIGIT_SUM",
                            "DOUBLE_THE_DIFFERENCE",
                            "DO_ALGEBRA",
                            "EAT",
                            "ENCODE",
                            "ENCRYPT",
                            "EVEN_ODD_COUNT",
                            "EVEN_ODD_PALINDROME",
                            "EXCHANGE",
                            "FACTORIAL",
                            "FACTORIZE",
                            "FIB",
                            "FIB4",
                            "FIBFIB",
                            "FILE_NAME_CHECK",
                            "FILTER_BY_PREFIX",
                            "FILTER_BY_SUBSTRING",
                            "FILTER_INTEGERS",
                            "FIND_CLOSEST_ELEMENTS",
                            "FIND_MAX",
                            "FIND_ZERO",
                            "FIX_SPACES",
                            "FIZZ_BUZZ",
                            "FLIP_CASE",
                            "FRUIT_DISTRIBUTION",
                            "GENERATE_INTEGERS",
                            "GET_CLOSET_VOWEL",
                            "GET_MAX_TRIPLES",
                            "GET_ODD_COLLATZ",
                            "GET_POSITIVE",
                            "GET_ROW",
                            "GREATEST_COMMON_DIVISOR",
                            "HAS_CLOSE_ELEMENTS",
                            "HEX_KEY",
                            "HISTOGRAM",
                            "HOW_MANY_TIMES",
                            "INCR_LIST",
                            "INTERSECTION",
                            "INTERSPERSE",
                            "INT_TO_MINI_ROMAN",
                            "ISCUBE",
                            "IS_BORED",
                            "IS_EQUAL_TO_SUM_EVEN",
                            "IS_HAPPY",
                            "IS_MULTIPLY_PRIME",
                            "IS_NESTED",
                            "IS_PALINDROME",
                            "IS_PRIME",
                            "IS_SIMPLE_POWER",
                            "IS_SORTED",
                            "LARGEST_DIVISOR",
                            "LARGEST_PRIME_FACTOR",
                            "LARGEST_SMALLEST_INTEGERS",
                            "LONGEST",
                            "MAKE_A_PILE",
                            "MAKE_PALINDROME",
                            "MATCH_PARENS",
                            "MAXIMUM_K",
                            "MAX_ELEMENT",
                            "MAX_FILL",
                            "MEAN_ABSOLUTE_DEVIATION",
                            "MEDIAN",
                            "MIN_PATH",
                            "MIN_SUBARRAY_SUM",
                            "MODP",
                            "MONOTONIC",
                            "MOVE_ONE_BALL",
                            "MULTIPLY",
                            "NEXT_SMALLEST",
                            "NUMERICAL_LETTER_GRADE",
                            "ODD_COUNT",
                            "ORDER_BY_POINTS",
                            "PAIRS_SUM_TO_ZERO",
                            "PARSE_MUSIC",
                            "PARSE_NESTED_PARENS",
                            "PLUCK",
                            "PRIME_FIB",
                            "PRIME_LENGTH",
                            "PROD_SIGNS",
                            "REMOVE_DUPLICATES",
                            "REMOVE_VOWELS",
                            "RESCALE_TO_UNIT",
                            "REVERSE_DELETE",
                            "RIGHT_ANGLE_TRIANGLE",
                            "ROLLING_MAX",
                            "ROUNDED_AVG",
                            "SAME_CHARS",
                            "SEARCH",
                            "SELECT_WORDS",
                            "SEPARATE_PAREN_GROUPS",
                            "SIMPLIFY",
                            "SKJKASDKD",
                            "SMALLEST_CHANGE",
                            "SOLUTION",
                            "SOLVE",
                            "SOLVE_STRING",
                            "SORTED_LIST_SUM",
                            "SORT_ARRAY",
                            "SORT_ARRAY_BINARY",
                            "SORT_EVEN",
                            "SORT_NUMBERS",
                            "SORT_THIRD",
                            "SPECIAL_FACTORIAL",
                            "SPECIAL_FILTER",
                            "SPLIT_WORDS",
                            "STARTS_ONE_ENDS",
                            "STRANGE_SORT_LIST",
                            "STRING_SEQUENCE",
                            "STRING_TO_MD5",
                            "STRING_XOR",
                            "STRLEN",
                            "STRONGEST_EXTENSION",
                            "SUM_PRODUCT",
                            "SUM_SQUARED_NUMS",
                            "SUM_SQUARES",
                            "SUM_TO_N",
                            "TOTAL_MATCH",
                            "TRI",
                            "TRIANGLE_AREA",
                            "TRIANGLE_AREA_2",
                            "TRIPLES_SUM_TO_ZERO",
                            "TRUNCATE_NUMBER",
                            "UNIQUE",
                            "UNIQUE_DIGITS",
                            "VALID_DATE",
                            "VOWELS_COUNT",
                            "WILL_IT_FLY",
                            "WORDS_IN_SENTENCE",
                            "WORDS_STRINGS",
                            "X_OR_Y",])]
    
    ### LLM Related
    model_token_limit = 4097
    chat_cache_folder=Path(__file__).parent / 'cache' / 'chat_cache'

    gpt4_model = ('gpt-4o', 'https://api.openai.com/v1')
    deepseek_model = ('deepseek-ai/DeepSeek-V3', 'https://api.siliconflow.cn/v1')

    ### Algorithm Related
    stop_on_first_plausible_patch = False
    # Ciallo related
    ciallo_max_fpps_try_per_mode = 3 # First Plausible Patch Search
    ciallo_max_mpps_try_per_mode = 3 # Plausible Patch Multiplication
    ciallo_prompt_token_limit = 1500
    ciallo_total_token_limit_target = 3000
    ciallo_code_token_limit = 3000
    ciallo_max_sample_count = 1 # Deepseek is only accept that n is 1
    ciallo_similarity_threshold = 0.5
    ciallo_max_rounds = 22
    ciallo_max_correct_time = 1
    ciallo_max_use_global_info_try = 5
    ciallo_max_patch_limit = 15
    ciallo_bf_token_limit = 2048
    # BaseLLM related
    basellm_prompt_token_limit = 1500
    basellm_total_token_limit_target = 3000
    basellm_max_sample_count = 50 # Deepseek is only accept that n is 1
    basellm_max_rounds = 22

    ### Logging Parameters ###
    logging_level=logging.INFO
