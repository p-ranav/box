import logging


class BranchNode:
    def __init__(self, box, true_case, false_case, generator):
        self.box = box
        self.true_case = true_case
        self.false_case = false_case
        self.generator = generator
        logging.debug("Constructing branch node")

    def to_python(self, indent="    "):
        logging.debug("Generating Python for branch node")

        assert len(self.box.input_data_flow_ports) == 1
        input_port = self.generator._find_destination_connection(
            self.box.input_data_flow_ports[0], "left"
        )
        condition_box = self.generator.port_box_map[input_port]

        # Find temp_results from condition_box
        condition_result_name = ""
        if condition_box in self.generator.temp_results:
            condition_result_name = self.generator.temp_results[condition_box]
            logging.debug("Condition result is named: " + condition_result_name)
        else:
            # The previous box is embedded as the branch condition
            # Generate the code for this box and embed it in place
            node = self.generator._create_node(condition_box)
            condition_result_name = node.to_python(
                "", store_result_in_variable=False, called_by_next_box=True
            ).strip()
            logging.debug("Condition expression: " + condition_result_name)

        result = indent + "if " + condition_result_name + ":\n"
        for statement in self.true_case:
            result += statement.to_python(indent + "    ")

        if len(self.false_case) > 0:
            logging.debug("Branch has a FALSE case")
            result += indent + "else:\n"
            for statement in self.false_case:
                result += statement.to_python(indent + "    ")

        return result
