from box.token import Token
import logging


class WhileLoopNode:
    def __init__(self, box, loop_body, generator):
        self.box = box
        self.generator = generator
        self.loop_body = loop_body
        logging.debug("Constructed while loop node")

    def to_python(self, indent="    "):
        logging.debug("Generating Python for while loop node")
        result = indent + "while "
        assert len(self.box.input_data_flow_ports) == 1  # the while condition

        input_port_0 = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[0], "left"
        )
        input_box = self.generator.port_box_map[input_port_0]
        condition = self.generator._get_output_data_name(input_box, input_port_0)

        logging.debug("  While condition: " + condition)

        result += condition + ":\n"

        logging.debug("  While loop body has " + str(len(self.loop_body)) + " boxes")

        for statement in self.loop_body:
            result += statement.to_python(indent + "    ")

        return result
