import re
from box.token import Token


class FunctionDeclarationNode:
    def __init__(self, box, parser):
        self.box = box
        self.parser = parser

    def to_python(self, indent="    "):
        # Function signature
        result = "def "
        function_name = self.box.box_header
        function_name = function_name[2 : len(function_name) - 1]
        function_name = re.sub("[\W_]", "", function_name)
        result += function_name

        self.parser.function_name = function_name

        result += "("
        box_contents = self.box.box_contents.split("\n")

        parameters = []
        for line in self.box.box_contents.split("\n"):
            if line.endswith(Token.DATA_FLOW_PORT):
                parameters.append(line[:-1].strip())

        for i, param in enumerate(parameters):
            result += param
            if i < len(parameters) - 1:
                result += ", "

        result += "):\n"
        return result
