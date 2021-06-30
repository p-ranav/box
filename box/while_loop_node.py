from box.token import Token


class WhileLoopNode:
    def __init__(self, box, loop_body, generator):
        self.box = box
        self.generator = generator
        self.loop_body = loop_body

    def to_python(self, indent="    "):
        result = indent + "while "

        assert len(self.box.input_data_flow_ports) == 1  # the while condition

        input_port_0 = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[0], "left"
        )
        input_box = self.generator.port_box_map[input_port_0]

        # Check if the previous box is either
        # - OperatorNode
        # - FunctionCallNode
        # In these cases,
        # Wrap the previous data flow box and get its emitted python code
        # This is the WhileLoop condition
        is_operator = self.generator._is_operator(input_box.box_contents)
        is_function = input_box.box_header.startswith(Token.FUNCTION_START)
        is_function_call = is_function and len(input_box.input_control_flow_ports) == 1

        condition = ""

        if is_operator or is_function_call:
            condition = (
                self.generator._create_node(input_box)
                .to_python(
                    indent="",
                    store_result_in_variable=False,
                    called_by_next_box=True,
                )
                .strip()
            )
        else:
            condition = self.generator._get_output_data_name(input_box, input_port_0)

        result += condition + ":\n"

        for statement in self.loop_body:
            result += statement.to_python(indent + "    ")

        return result
