class FunctionCallNode:
    def __init__(self, box, parser):
        self.box = box
        self.parser = parser
        self._result_prefix = "fn"

    def to_python(
        self, indent="    ", store_result_in_variable=True, called_by_next_box=False
    ):
        result = ""

        # Check if the next box is a while loop
        # If so, do not emit any code unless forced
        if self.parser._is_next_box_a_while_loop(self.box):
            if not called_by_next_box:
                return result

        result = indent

        function_name = self.box.box_header
        function_name = function_name[2 : len(function_name) - 1]

        function_args = []

        for port in self.box.input_data_flow_ports:
            input_port = self.parser._find_destination_connection(port, "left")
            input_box = self.parser.port_box_map[input_port]
            function_args.append(
                self.parser._get_output_data_name(input_box, input_port)
            )

        # Check if function result is used
        if store_result_in_variable and len(self.box.output_data_flow_ports) > 0:
            fn_result = self._result_prefix + "_" + self.box.uuid_short() + "_result"
            self.parser.temp_results[self.box] = fn_result
            result += fn_result + " = "

        result += function_name
        result += "("
        for i, arg in enumerate(function_args):
            result += arg
            if i < len(function_args) - 1:
                result += ", "

        result += ")\n"
        return result
