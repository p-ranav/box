from box.token import Token
import logging
import re


class FunctionDeclarationNode:
    def __init__(self, box, generator):
        self.box = box
        self.generator = generator
        logging.debug("Constructed function declaration node")

    def to_python(self, indent="    "):
        logging.debug("Generating Python for function declaration node")
        # Function signature
        result = "def "
        function_name = self.box.box_header
        function_name = function_name[2 : len(function_name) - 1]
        function_name = re.sub("[\W_]", "", function_name)
        result += function_name

        logging.debug("  Function name: " + function_name)

        self.generator.function_name = function_name

        result += "("
        box_contents = self.box.box_contents.split("\n")

        parameters = []
        for line in self.box.box_contents.split("\n"):
            if line.endswith(Token.DATA_FLOW_PORT):
                parameters.append(line[:-1].strip())

        logging.debug("  Function takes " + str(len(parameters)) + " parameters")

        for i, param in enumerate(parameters):
            result += param
            if i < len(parameters) - 1:
                result += ", "

        result += "):\n"
        return result
