from box_parser import detect_boxes, build_parse_tree
from nodes.string_literal_node import StringLiteralNode
from nodes.inputs_node import InputsNode
from nodes.outputs_node import OutputsNode
from nodes.function_call_node import FunctionCallNode

import box_type
import re
import sys

def build_executable_function(root):
    excutable_boxes = []
    function_has_inputs = any([child.box_info.name == "Inputs" for child in root.children])

    def next(boxes, root):
        result = []
        for box in boxes:
            output_ports = box.output_ports
            for port in output_ports:
                next_box_uuid, next_port_uuid = root.src2dst_connections[(box.uuid, port.uuid)]
                result.extend(filter(lambda x: x.uuid == next_box_uuid, root.children))
        return result

    def prev(boxes, root):
        result = []
        for box in boxes:
            input_ports = reversed(box.input_ports)
            for port in input_ports:
                prev_box_uuid, prev_port_uuid = root.dst2src_connections[(box.uuid, port.uuid)]
                result.extend(filter(lambda x: x.uuid == prev_box_uuid, root.children))
        return result

    def find_box(boxes, uuid):
        for box in boxes:
            if box.uuid == uuid:
                return box
        return None

    inputs = []
    if function_has_inputs:
        inputs = [child for child in root.children if child.box_info.name == "Inputs"]
        assert len(inputs) == 1
    else:
        inputs = [child for child in root.children if len(child.input_ports) == 0]
        inputs = [i for i in inputs if i.node_type != box_type.BOX_TYPE_COMMENT]
        assert len(inputs) >= 1

    order_of_operations = []

    start = inputs
    while True:
        next_boxes = next(start, root)
        order_of_operations.extend(start)
        
        prev_boxes = prev(next_boxes, root)
        for box in prev_boxes:
            if box not in order_of_operations:
                order_of_operations.append(box)            
        start = next_boxes
        if len(start) == 0:
            break

    nodes = []
    constant_names = {} # {<box>: "constant_<index>", ...}
    constant_index = 0
    for i, o in enumerate(order_of_operations):
        if o.box_info.name == "Inputs":
            nodes.append(InputsNode(o))
        elif o.node_type in [box_type.BOX_TYPE_STRING_LITERAL, box_type.BOX_TYPE_NUMERIC]:
            nodes.append(StringLiteralNode(o, "constant_" + str(constant_index), o.box_info.name))
            constant_names[o] = "constant_" + str(constant_index)
            constant_index += 1
        elif o.node_type == box_type.BOX_TYPE_FUNCTION:
            possible_inputs_to_this_function = order_of_operations[:i]
            call_args = []
            for p in reversed(o.input_ports):
                input_box_uuid, input_port_uuid = root.dst2src_connections[o.uuid, p.uuid]
                call_args.append([find_box(root.children, input_box_uuid), input_port_uuid])

            call_arg_strings = []
            for arg in call_args:
                arg_box = arg[0]
                arg_port_uuid = arg[1]

                if arg_box.box_info.name == "Inputs":
                    # input is connected to this call
                    # check which port is connected
                    port_index = [port.uuid for port in reversed(arg_box.output_ports)].index(arg_port_uuid)
                    call_arg_strings.append("param_" + str(port_index))
                elif arg_box.node_type in [box_type.BOX_TYPE_NUMERIC, box_type.BOX_TYPE_STRING_LITERAL]:
                    call_arg_strings.append(constant_names[arg_box])
                elif arg_box.node_type == box_type.BOX_TYPE_FUNCTION:
                    # function output is connected to this call
                    function_name = arg_box.box_info.name
                    function_output_name = function_name + "_result"
                    call_arg_strings.append(function_output_name)                
            nodes.append(FunctionCallNode(o, o.box_info.name, call_arg_strings, len(o.output_ports) > 0))
        elif o.box_info.name == "Outputs":
            output_args = []
            for p in reversed(o.input_ports):
                input_box_uuid, input_port_uuid = root.dst2src_connections[o.uuid, p.uuid]
                output_args.append([find_box(root.children, input_box_uuid), input_port_uuid])            

            return_val_strings = []
            for arg in output_args:
                arg_box = arg[0]
                arg_port_uuid = arg[1]            

                if arg_box.box_info.name == "Inputs":
                    # input is connected to this call
                    # check which port is connected
                    port_index = [port.uuid for port in reversed(arg_box.output_ports)].index(arg_port_uuid)
                    return_val_strings.append("param_" + str(port_index))            
                elif arg_box.node_type in [box_type.BOX_TYPE_NUMERIC, box_type.BOX_TYPE_STRING_LITERAL]:
                    return_val_strings.append(constant_names[arg_box])
                elif arg_box.node_type == box_type.BOX_TYPE_FUNCTION:
                    # function output is connected to this call
                    function_name = arg_box.box_info.name
                    function_output_name = function_name + "_result"
                    return_val_strings.append(function_output_name)
            
            nodes.append(OutputsNode(o, return_val_strings))

    # Serialize to Python
    function_name = root.box_info.name
    function_name = re.sub(r'\W+', '', function_name)
    result = "def " + function_name

    if function_has_inputs:
        result += nodes[0].to_python()
        result += ":\n"
        nodes = nodes[1:]
    else:
        result += "():\n"

    for n in nodes:
        result += "    " + n.to_python() + "\n"

    print(result)

def main(filename):
    lines, boxes = detect_boxes(filename)
    root = build_parse_tree(lines, boxes)
    root_type = root.node_type
    if root_type == box_type.BOX_TYPE_FUNCTION:
        build_executable_function(root)

if __name__ == "__main__":
    main(sys.argv[1])
