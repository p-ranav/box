class ForLoopNode:
    def __init__(self, box, loop_body, generator):
        self.box = box
        self.generator = generator
        self.loop_body = loop_body

    def to_python(self, indent="    "):
        result = indent + "for "

        assert len(self.box.input_data_flow_ports) == 3

        input_port_0 = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[0], "left"
        )
        input_port_1 = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[1], "left"
        )
        input_port_2 = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[2], "left"
        )

        loop_arguments = []
        for i, port in enumerate([input_port_0, input_port_1, input_port_2]):
            box = self.generator.port_box_map[port]
            loop_arguments.append(self.generator._get_output_data_name(box, port))

        start_index, end_index, step = loop_arguments

        current_index = "index_" + self.box.uuid_short()
        self.generator.temp_results[self.box] = current_index

        result += (
            current_index
            + " in range("
            + start_index
            + ", "
            + end_index
            + ", "
            + step
            + "):\n"
        )

        for statement in self.loop_body:
            result += statement.to_python(indent + "    ")

        return result
