class ReturnNode:
    def __init__(self, box, parser):
        self.box = box
        self.parser = parser

    def to_python(self, indent="    "):
        result = indent + "return"

        return_vals = []

        for port in self.box.input_data_flow_ports:
            input_port = self.parser._find_destination_connection(port, "left")
            input_box = self.parser.port_box_map[input_port]
            return_vals.append(self.parser._get_output_data_name(input_box, input_port))

        for i, val in enumerate(return_vals):
            result += " " + val
            if i < len(return_vals) - 1:
                result += ", "
        result += "\n"

        return result
