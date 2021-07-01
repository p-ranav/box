class ForEachNode:
    def __init__(self, box, loop_body, generator):
        self.box = box
        self.generator = generator
        self.loop_body = loop_body
        self._result_prefix = "value"

    def to_python(self, indent="    "):
        result = indent + "for "

        assert len(self.box.input_data_flow_ports) == 1

        input_port_0 = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[0], "left"
        )
        input_box = self.generator.port_box_map[input_port_0]
        input_iterable = self.generator._get_output_data_name(input_box, input_port_0)

        current_index = self._result_prefix + "_" + self.box.uuid_short()
        self.generator.temp_results[self.box] = current_index

        result += current_index + " in " + input_iterable + ":\n"

        for statement in self.loop_body:
            result += statement.to_python(indent + "    ")

        return result
