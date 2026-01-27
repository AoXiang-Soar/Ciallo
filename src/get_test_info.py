import re

import user_params


def extract_test_function(file_path, function_name):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n') for line in f.readlines()]

    # Step 1: Find the start line of the target function
    start_line_index = -1
    function_pattern = re.compile(r'\bvoid\s+' + re.escape(function_name) + r'\s*\(')
    block_comment = False

    for i, line in enumerate(lines):
        current_line = line
        in_block_comment = block_comment
        stripped = []
        in_string = None
        escape = False
        chars = iter(current_line)
        for c in chars:
            if in_block_comment:
                if c == '*':
                    next_c = next(chars, None)
                    if next_c == '/':
                        in_block_comment = False
                continue
            if in_string is not None:
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == in_string:
                    in_string = None
                stripped.append(c)
                continue
            if c == '/':
                next_c = next(chars, None)
                if next_c == '*':
                    in_block_comment = True
                    continue
                elif next_c == '/':
                    break
                else:
                    stripped.append(c)
                    if next_c is not None:
                        stripped.append(next_c)
            elif c in ('"', "'"):
                in_string = c
                stripped.append(c)
            else:
                stripped.append(c)
        # Update block_comment for next line
        block_comment = in_block_comment
        # Check if the stripped line matches the function pattern
        if function_pattern.search(''.join(stripped)):
            start_line_index = i
            break

    if start_line_index == -1:
        return None

    # Step 2: Collect the entire function body by tracking braces
    function_lines = []
    current_brace_level = 0
    block_comment = False
    in_string = None
    escape = False
    found_end = False

    for line_num in range(start_line_index, len(lines)):
        line = lines[line_num]
        new_line = []
        chars = iter(line)
        for c in chars:
            if block_comment:
                if c == '*':
                    next_c = next(chars, None)
                    if next_c == '/':
                        block_comment = False
                continue
            if in_string is not None:
                new_line.append(c)
                if escape:
                    escape = False
                elif c == '\\':
                    escape = True
                elif c == in_string:
                    in_string = None
                continue
            if c == '/':
                next_c = next(chars, None)
                if next_c == '*':
                    block_comment = True
                    continue
                elif next_c == '/':
                    new_line.extend([c, next_c] if next_c else [c])
                    break
                else:
                    if next_c is not None:
                        new_line.extend([c, next_c])
                    else:
                        new_line.append(c)
            elif c in ('"', "'"):
                in_string = c
                new_line.append(c)
            elif c == '{':
                if not block_comment and in_string is None:
                    current_brace_level += 1
                    new_line.append(c)
            elif c == '}':
                if not block_comment and in_string is None:
                    current_brace_level -= 1
                    new_line.append(c)
                    if current_brace_level == 0:
                        found_end = True
                        break
            else:
                new_line.append(c)
        # Join the processed characters (for brace counting) but keep original line
        function_lines.append(line)
        if found_end:
            break

    return '\n'.join(function_lines)

def get_hej_test_function(project_name, project_id, test_suite, test_name):
    test_path = 'src/test/java/humaneval'
    file_path = f'{user_params.UserParams.HEJ_TMP_DIR}/{project_name}-{project_id}/{test_path}/{test_suite.replace('.', '/')}.java'
    return extract_test_function(file_path, test_name)

def get_test_function(project_name, project_id, test_suite, test_name):
    if project_name == 'humanevaljava':
        return get_hej_test_function(project_name, project_id, test_suite, test_name)
    if test_suite == '' or test_name == '':
        return ''
    if project_name == 'Compress' and project_id == 7:
        return '''    public void testRoundTripNames(){
        checkName("");
        checkName("The quick brown fox\n");
        checkName("\177");
        // checkName("\0"); // does not work, because NUL is ignored
        // COMPRESS-114
        checkName("0302-0601-3   F06 W220 ZB LALALA          CAN  DC   04 060302 MOE.model");
    }'''
    elif project_name == 'Compress' and project_id == 8:
        return '''    public void testParseOctalInvalid() throws Exception{
        byte [] buffer;
        buffer=new byte[0]; // empty byte array
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException - should be at least 2 bytes long");
        } catch (IllegalArgumentException expected) {
        }
        buffer=new byte[]{0}; // 1-byte array
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException - should be at least 2 bytes long");
        } catch (IllegalArgumentException expected) {
        }
        buffer=new byte[]{0,0,' '}; // not all NULs
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException - not all NULs");
        } catch (IllegalArgumentException expected) {
        }
        buffer=new byte[]{' ',0,0,0}; // not all NULs
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException - not all NULs");
        } catch (IllegalArgumentException expected) {
        }
        buffer = "abcdef ".getBytes("UTF-8"); // Invalid input
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException");
        } catch (IllegalArgumentException expected) {
        }
        buffer = "77777777777".getBytes("UTF-8"); // Invalid input - no trailer
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException - no trailer");
        } catch (IllegalArgumentException expected) {
        }
        buffer = " 0 07 ".getBytes("UTF-8"); // Invalid - embedded space
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException - embedded space");
        } catch (IllegalArgumentException expected) {
        }
        buffer = " 0\\00007 ".getBytes("UTF-8"); // Invalid - embedded NUL
        try {
            TarUtils.parseOctal(buffer,0, buffer.length);
            fail("Expected IllegalArgumentException - embedded NUL");
        } catch (IllegalArgumentException expected) {
        }
    }'''
    base_dir_of_tests = {'Chart': 'tests',
                         'Cli': 'src/test',
                         'Closure': 'test',
                         'Codec': 'src/test',
                         'Collections': 'src/test',
                         'Compress': 'src/test/java',
                         'Csv': 'src/test/java',
                         'Gson': 'gson/src/test/java',
                         'JacksonCore': 'src/test/java',
                         'JacksonDatabind': 'src/test/java',
                         'JacksonXml': 'src/test/java',
                         'Jsoup': 'src/test/java',
                         'JxPath': 'src/test',
                         'Lang': 'src/test',
                         'Math': 'src/test',
                         'Mockito': 'test',
                         'Time': 'src/test/java'}
    d4j = user_params.UserParams.D4J_TMP_DIR
    test_path = base_dir_of_tests[project_name]
    if project_name == 'Lang' and project_id in [57]:
        test_path = 'src/test'
    try:
        file_path = f'{d4j}/{project_name}-{project_id}/{test_path}/{test_suite.replace('.', '/')}.java'
        return extract_test_function(file_path, test_name)
    except Exception as e:
        if project_name in ['Cli', 'Codec', 'Collections', 'Lang', 'Math']:
            test_path = 'src/test/java'
        else:
            test_path = 'src/test/java'
        file_path = f'{d4j}/{project_name}-{project_id}/{test_path}/{test_suite.replace('.', '/')}.java'
        return extract_test_function(file_path, test_name)


def extract_failed_tests(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    failed_tests = set()
    i = 0
    while i < len(lines):
        if lines[i].startswith('---'):
            if i + 1 < len(lines):
                group = lines[i] + lines[i + 1]
                failed_tests.add(group)
                i += 2
            else:
                failed_tests.add(lines[i])
                i += 1
        else:
            i += 1
    return failed_tests