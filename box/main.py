from box_parser import detect_boxes, build_parse_tree
import box_type
import re
import sys

class BoxFunctionInvocation:
    def __init__(self, name, *args):
        self.name = name
        self.args = args

    def to_python(self):
        result = self.name + '('
        for i, arg in enumerate(self.args):
            result += arg
            if i < len(self.args) - 1:
                result += ', '
        result += ')'
        return result

class ConstantDeclaration:
    def __init__(self, node_ref, name, value):
        self.node_ref = node_ref
        self.name = name
        self.value = value

    def to_python(self):
        return self.name + ' = ' + str(self.value)

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

    print([n.box_info.name for n in order_of_operations])

def main(filename):
    lines, boxes = detect_boxes(filename)
    root = build_parse_tree(lines, boxes)
    root_type = root.node_type
    if root_type == box_type.BOX_TYPE_FUNCTION:
        build_executable_function(root)

if __name__ == "__main__":
    main(sys.argv[1])
