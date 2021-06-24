from box_parser import detect_boxes, build_parse_tree
import box_type
import re
import sys

class BoxFunction:
    def __init__(self, name, inputs):
        self.name = name
        self.inputs = inputs

    def to_python(self):
        result  = 'def ' + self.name + '('
        for i, arg in enumerate(self.inputs):
            result += arg
            if i < len(self.inputs) - 1:
                result += ', '
        result += '):\n'
        result += '    ' + 'pass'
        return result

def main(filename):
    lines, boxes = detect_boxes(filename)
    root = build_parse_tree(lines, boxes)
    root_type = root.node_type
    if root_type == box_type.BOX_TYPE_FUNCTION:
        # Box is a function declaration
        function_name = root.box_info.name
        function_name = re.sub(r'\W+', '', function_name)

        # children with indegree = 0
        root_children = [child for child in root.children if len(child.input_ports) == 0]
        
        children_uuid_dict = {}
        for child in root.children:
            children_uuid_dict[child.uuid] = child

        # Find all child boxes without input ports
        function_inputs = [box for box in root_children if box.box_info.name == "Inputs"]
        if len(function_inputs):
            assert len(function_inputs) == 1
            box_contents = function_inputs[0].box_info.contents
            box_contents = box_contents.split("\n")
            function_inputs = []
            for line in box_contents:
                if len(line):
                    assert line.endswith(" ○")
                    function_inputs.append(line.split(" ○")[0].strip())
            
        function = BoxFunction(function_name, function_inputs)
        print(function.to_python())
            
if __name__ == "__main__":
    main(sys.argv[1])
