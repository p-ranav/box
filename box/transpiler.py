
class Transpiler:
    def __init__(self, root_function_declaration_box):
        self.root = root_function_declaration_box
        self.has_inputs = any([child.box_info.name == "Inputs" for child in self.root.children])

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

    def get_inputs(self):
        # Returns `Inputs` if this function has inputs
        # else, returns all zero-indegree child boxes
        result = []
        if function_has_inputs:
            result = [child for child in root.children if child.box_info.name == "Inputs"]
            assert len(inputs) == 1
        else:
            result = [child for child in root.children if len(child.input_ports) == 0]
            result = [i for i in inputs if i.node_type != box_type.BOX_TYPE_COMMENT]
            assert len(inputs) >= 1
            return result

    def get_order_of_operations(self):
        result = []
        
        start = self.get_inputs()
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

    def to_python(self):
        pass
        
    
        
