import box_type
from nodes.inputs_node import InputsNode
from nodes.constant_node import ConstantNode
from nodes.outputs_node import OutputsNode
from nodes.function_call_node import FunctionCallNode
import re

class Transpiler:
    def __init__(self, root_function_declaration_box):
        self.root = root_function_declaration_box
        self.has_inputs = any([child.box_info.name == "Inputs" for child in self.root.children])
        self.nodes = [] # list of AST nodes

        # State variables
        self.constant_names = {} # map of {<box_1>: "constant_name_1", <box_2>: "constant_name_2", ...}
        self.constant_index = 0  # current number of constants

    def next(self, boxes):
        result = []
        for box in boxes:
            output_ports = box.output_ports
            for port in output_ports:
                next_box_uuid, next_port_uuid = self.root.src2dst_connections[(box.uuid, port.uuid)]
                result.extend(filter(lambda x: x.uuid == next_box_uuid, self.root.children))
        return result

    def prev(self, boxes):
        result = []
        for box in boxes:
            for port in box.input_ports:
                prev_box_uuid, prev_port_uuid = self.root.dst2src_connections[(box.uuid, port.uuid)]
                result.extend(filter(lambda x: x.uuid == prev_box_uuid, self.root.children))
        return result

    def find_box(self, boxes, uuid):
        for box in boxes:
            if box.uuid == uuid:
                return box
        return None

    def get_order_of_operations(self):
        result = []

        # Need to start somewhere
        # Check if this function has inputs
        inputs = []
        if self.has_inputs:
            inputs = [child for child in self.root.children if child.box_info.name == "Inputs"]
            assert len(inputs) == 1
        else:
            # Function takes no inputs
            # Find all zero-indegree boxes
            inputs = [child for child in self.root.children if len(child.input_ports) == 0]
            inputs = [i for i in inputs if i.box_type != box_type.BOX_TYPE_COMMENT]
            assert len(inputs) >= 1
        
        start = inputs
        while True:
            next_boxes = self.next(start)
            result.extend(start)
        
            prev_boxes = self.prev(next_boxes)
            for box in prev_boxes:
                if box not in result:
                    result.append(box)            
            start = next_boxes
            if len(start) == 0:
                break

        return result

    def is_inputs(self, box):
        return box.box_info.name == "Inputs"

    def add_inputs_node(self, box):
        self.nodes.append(InputsNode(box))

    def is_constant(self, box):
        return box.box_type in [
            box_type.BOX_TYPE_STRING_LITERAL,
            box_type.BOX_TYPE_NUMERIC
        ]

    def add_constant_node(self, box):
        self.nodes.append(ConstantNode(box, "constant_" + str(self.constant_index), box.box_info.name))
        self.constant_names[box] = "constant_" + str(self.constant_index)
        self.constant_index += 1

    def is_function(self, box):
        return box.box_type == box_type.BOX_TYPE_FUNCTION

    def add_function_call_node(self, box, possible_inputs_to_this_function):

        # Build a list of arguments (boxes) to this function call
        call_args = []
        for port in box.input_ports:
            input_box_uuid, input_port_uuid = self.root.dst2src_connections[box.uuid, port.uuid]
            call_args.append([self.find_box(self.root.children, input_box_uuid), input_port_uuid])

        # Build a list of strings, for each box in call_args, i.e., the call arguments

        call_arg_strings = []
        for arg in call_args:
            arg_box = arg[0]
            arg_port_uuid = arg[1]

            if self.is_inputs(arg_box):
                # input is connected to this call
                # check which port is connected
                port_index = [port.uuid for port in arg_box.output_ports].index(arg_port_uuid)
                call_arg_strings.append("param_" + str(port_index))
            elif self.is_constant(arg_box):
                call_arg_strings.append(self.constant_names[arg_box])
            elif self.is_function(arg_box):
                # function output is connected to this call
                function_name = arg_box.box_info.name
                function_output_name = function_name + "_result"
                call_arg_strings.append(function_output_name)
                
        self.nodes.append(FunctionCallNode(box, box.box_info.name, call_arg_strings))

    def is_outputs(self, box):
        return box.box_info.name == "Outputs"

    def add_output_node(self, box):

        # Build list of outputs (boxes) to be returned by the `root` function
        output_args = []
        for port in box.input_ports:
            input_box_uuid, input_port_uuid = self.root.dst2src_connections[box.uuid, port.uuid]
            output_args.append([self.find_box(self.root.children, input_box_uuid), input_port_uuid])

        return_val_strings = []
        for arg in output_args:
            arg_box = arg[0]
            arg_port_uuid = arg[1]            
            
            if self.is_inputs(arg_box):
                # input is connected to this call
                # check which port is connected
                port_index = [port.uuid for port in arg_box.output_ports].index(arg_port_uuid)
                return_val_strings.append("param_" + str(port_index))            
            elif self.is_constant(arg_box):
                return_val_strings.append(self.constant_names[arg_box])
            elif self.is_function(arg_box):
                # function output is connected to this call
                function_name = arg_box.box_info.name
                function_output_name = function_name + "_result"
                return_val_strings.append(function_output_name)
            
        self.nodes.append(OutputsNode(box, return_val_strings))

    def build_node_list(self, list_of_boxes):
        # Converts each box to an AST node object
        for i, box in enumerate(list_of_boxes):
            if self.is_inputs(box):
                self.add_inputs_node(box)
            elif self.is_constant(box):
                self.add_constant_node(box)
            elif self.is_function(box):
                self.add_function_call_node(box, possible_inputs_to_this_function=list_of_boxes[:i])
            elif self.is_outputs(box):
                self.add_output_node(box)
            else:
                pass

    def to_python(self):
        self.build_node_list(self.get_order_of_operations())
        # now self.nodes has all the nodes

        function_name = self.root.box_info.name
        function_name = re.sub(r'\W+', '', function_name)
        result = "def " + function_name
        
        if self.has_inputs:
            result += self.nodes[0].to_python()
            result += ":\n"
            self.nodes = self.nodes[1:]
        else:
            result += "():\n"

        for n in self.nodes:
            result += "    " + n.to_python() + "\n"

        return result
        
