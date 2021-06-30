class OperatorNode:

    # Arithmetic operators
    OPERATOR_TOKEN_ADD = "+"
    OPERATOR_TOKEN_SUBTRACT = "-"
    OPERATOR_TOKEN_MULTIPLY = "*"
    OPERATOR_TOKEN_DIVIDE = "/"
    OPERATOR_TOKEN_MODULO = "%"
    OPERATOR_TOKEN_EXPONENTIATION = "**"
    OPERATOR_TOKEN_FLOOR_DIVISION = "//"

    # Logical operators
    OPERATOR_TOKEN_AND = "&&"
    OPERATOR_TOKEN_OR = "||"
    OPERATOR_TOKEN_NOT = "!"

    # Comparison operators
    OPERATOR_TOKEN_GREATER_THAN = ">"
    OPERATOR_TOKEN_GREATER_THAN_OR_EQUAL = ">="
    OPERATOR_TOKEN_LESS_THAN = "<"
    OPERATOR_TOKEN_LESS_THAN_OR_EQUAL = "<="
    OPERATOR_TOKEN_EQUAL = "=="
    OPERATOR_TOKEN_NOT_EQUAL = "!="

    UNARY_OPERATORS = [OPERATOR_TOKEN_NOT]

    BINARY_OPERATORS = [
        OPERATOR_TOKEN_ADD,
        OPERATOR_TOKEN_SUBTRACT,
        OPERATOR_TOKEN_MULTIPLY,
        OPERATOR_TOKEN_DIVIDE,
        OPERATOR_TOKEN_MODULO,
        OPERATOR_TOKEN_EXPONENTIATION,
        OPERATOR_TOKEN_FLOOR_DIVISION,
        OPERATOR_TOKEN_AND,
        OPERATOR_TOKEN_OR,
        OPERATOR_TOKEN_GREATER_THAN,
        OPERATOR_TOKEN_GREATER_THAN_OR_EQUAL,
        OPERATOR_TOKEN_LESS_THAN,
        OPERATOR_TOKEN_LESS_THAN_OR_EQUAL,
        OPERATOR_TOKEN_EQUAL,
        OPERATOR_TOKEN_NOT_EQUAL,
    ]

    def __init__(self, box, generator):
        self.box = box
        self.generator = generator
        self._result_prefix = "op"

    def to_python(
        self, indent="    ", store_result_in_variable=True, called_by_next_box=False
    ):
        result = ""

        # Check number of input ports
        box_contents = self.generator._sanitize_box_contents(self.box.box_contents)

        operator = box_contents

        # Check if the next box is a while loop
        # If so, do not emit any code unless forced
        if self.generator._is_next_box_a_while_loop(self.box):
            if not called_by_next_box:
                return result

        if operator in OperatorNode.UNARY_OPERATORS:
            assert len(self.box.input_data_flow_ports) == 1

            input_port_0 = self.generator._find_destination_connection(
                self.box.input_data_flow_ports[0], "left"
            )
            input_box = self.generator.port_box_map[input_port_0]

            argument = self.generator._get_output_data_name(input_box, input_port_0)

            if store_result_in_variable:
                operator_result = (
                    self._result_prefix + "_" + self.box.uuid_short() + "_result"
                )
                self.generator.temp_results[self.box] = operator_result
                result = indent + operator_result + " = "

            result += "(not " + argument + ")\n"

        elif operator in OperatorNode.BINARY_OPERATORS:
            # There must be exactly 2 input data flow ports for this node
            assert len(self.box.input_data_flow_ports) == 2

            input_port_0 = self.generator._find_destination_connection(
                self.box.input_data_flow_ports[0], "left"
            )
            input_port_1 = self.generator._find_destination_connection(
                self.box.input_data_flow_ports[1], "left"
            )

            operator_arguments = []
            for i, port in enumerate([input_port_0, input_port_1]):
                box = self.generator.port_box_map[port]
                operator_arguments.append(
                    self.generator._get_output_data_name(box, port)
                )

            lhs, rhs = operator_arguments

            # Find the two input boxes and parse their contents
            # Then set result to:
            #   <box_1_contents> <operator> <box_2_contents>
            #
            # Create a variable to store the result
            if store_result_in_variable:
                operator_result = (
                    self._result_prefix + "_" + self.box.uuid_short() + "_result"
                )
                self.generator.temp_results[self.box] = operator_result
                result = indent + operator_result + " = "

            result += "(" + lhs + " " + operator + " " + rhs + ")\n"

        return result
