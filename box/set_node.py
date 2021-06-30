class SetNode:
    def __init__(self, box, parser):
        self.box = box
        self.parser = parser

    def to_python(self, indent="    "):
        assert len(self.box.input_data_flow_ports) == 2

        input_port_0 = self.parser._find_destination_connection(
            self.box.input_data_flow_ports[0], "left"
        )
        input_port_1 = self.parser._find_destination_connection(
            self.box.input_data_flow_ports[1], "left"
        )

        set_arguments = []
        for i, port in enumerate([input_port_0, input_port_1]):
            box = self.parser.port_box_map[port]
            set_arguments.append(self.parser._get_output_data_name(box, port))

        lhs, rhs = set_arguments

        # Find the two input boxes and parse their contents
        # Then set result to:
        #   <box_1_contents> = <box_2_contents>
        #
        # Create a variable to store the result

        self.parser.temp_results[self.box] = lhs

        result = indent + lhs + " = " + rhs + "\n"

        return result
