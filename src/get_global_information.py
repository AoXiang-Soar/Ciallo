from tree_sitter import Parser

import src.tslang as tslang

FIELD_QUERY = "(field_declaration) @field"
METHOD_QUERY = ("""(method_declaration
  type_parameters: (type_parameters)? @type_params
  parameters: (formal_parameters) @params
) @method""")


class JavaParser:
    def __init__(self):
        lang = tslang.JAVA
        self.parser = Parser(lang)
        self.field_query = lang.query(FIELD_QUERY)
        self.method_query = lang.query(METHOD_QUERY)

    def parse_file(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        tree = self.parser.parse(bytes(code, 'utf-8'))
        return {
            'fields': self._extract_fields(tree.root_node, code),
            'methods': self._extract_methods(tree.root_node, code)
        }

    def _extract_fields(self, node, code):
        fields = []
        for _, captures in self.field_query.captures(node).items():
            for capture in captures:
                if type_node := capture.child_by_field_name('type'):
                    field_type = self._node_text(type_node, code)

                    for declarator in capture.children_by_field_name('declarator'):
                        if name_node := declarator.child_by_field_name('name'):
                            fields.append((
                                field_type.strip(),
                                self._node_text(name_node, code).strip()
                            ))
        return sorted(set(fields), key=lambda x: x[1])

    def _extract_methods(self, node, code):
        methods = []
        for _, captures in self.method_query.captures(node).items():
            for capture in captures:
                return_type = ""
                type_params = self._parse_type_params(capture, code)
                parameters = self._parse_parameters(capture, code)
                if type_node := capture.child_by_field_name('type'):
                    return_type = self._node_text(type_node, code).strip()

                if name_node := capture.child_by_field_name('name'):
                    methods.append((
                        return_type,
                        self._node_text(name_node, code).strip(),
                        type_params,
                        parameters
                    ))

        return sorted(set(methods), key=lambda x: x[1])

    def _parse_type_params(self, method_node, code):
        type_params_node = method_node.child_by_field_name('type_parameters')
        if not type_params_node:
            return ""
        return self._node_text(type_params_node, code)

    def _parse_parameters(self, method_node, code):
        params = []
        params_node = method_node.child_by_field_name('parameters')
        if params_node:
            for param_node in params_node.children:
                if param_node.type == 'formal_parameter':
                    param_type = self._get_child_text(param_node, 'type', code)
                    param_name = self._get_child_text(param_node, 'name', code)
                    if param_type and param_name:
                        params.append(f"{param_type} {param_name}")
                elif param_node.type == 'spread_parameter':
                    params.append(code[param_node.start_byte:param_node.end_byte])
        return ", ".join(params)

    def _get_class_name(self, method_node, code):
        current = method_node
        while current.parent:
            current = current.parent
            if current.type == 'class_declaration':
                name_node = current.child_by_field_name('name')
                return self._node_text(name_node, code)
        return ""

    def _get_child_text(self, node, field_name, code):
        child = node.child_by_field_name(field_name)
        return self._node_text(child, code) if child else ""

    def _node_text(self, node, code):
        tokens_index = tree_to_token_index(node)
        loc = code.split('\n')
        code_tokens = ''
        for x in tokens_index:
            code_tokens += index_to_code_token(x, loc)
        return code_tokens

def analyze(file_path):
    analyzer = JavaParser()
    results = analyzer.parse_file(file_path)

    text = 'Global Variables:\n'
    for var_type, var_name in results['fields']:
        text += f'\t{var_type} {var_name}\n'

    text += 'Methods:'
    for ret_type, method_name, type_params, parameters in results['methods']:
        signature = []
        if type_params:
            signature.append(type_params)
        signature.append(f"{method_name}({parameters})")

        if ret_type != "":
            signature.insert(0, ret_type)

        text += '\n\t' + ' '.join(signature)
    return text

def tree_to_token_index(root_node):
    if (len(root_node.children) == 0 or root_node.type.find('string') != -1) and root_node.type != 'comment':
        return [(root_node.start_point, root_node.end_point)]
    else:
        code_tokens = []
        for child in root_node.children:
            code_tokens += tree_to_token_index(child)
        return code_tokens


def index_to_code_token(index, code):
    start_point = index[0]
    end_point = index[1]
    if start_point[0] == end_point[0]:
        s = code[start_point[0]][start_point[1]:end_point[1]]
    else:
        s = ""
        s += code[start_point[0]][start_point[1]:]
        for i in range(start_point[0] + 1, end_point[0]):
            s += code[i]
        s += code[end_point[0]][:end_point[1]]
    return s
