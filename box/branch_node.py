class BranchNode:
    def __init__(self, box, true_case, false_case, generator):
        self.box = box
        self.true_case = true_case
        self.false_case = false_case
        self.generator = generator

    def to_python(self, indent="    "):
        assert len(self.box.input_data_flow_ports) == 1
        input_port = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[0], "left"
        )
        condition_box = self.generator.port_box_map[input_port]

        # Find temp_results from condition_box
        condition_result_name = self.generator.temp_results[condition_box]

        result = indent + "if " + condition_result_name + " == True:\n"
        for statement in self.true_case:
            result += statement.to_python(indent + "    ")

        result += indent + "else:\n"
        for statement in self.false_case:
            result += statement.to_python(indent + "    ")

        return result