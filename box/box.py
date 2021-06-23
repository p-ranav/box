import uuid

class Box:
    def __init__(self):
        self.box_info = None
        self.uuid = None
        self.parent_uuid = None
        self.node_type = ""     # function? constant?
        self.input_ports = []   # list of Port
        self.output_ports = []  # list of Port
        self.children = []      # list of Box
        self.connections = {}   # src -> dst Ports (guid) between boxes
                                # {(src.parent_uuid, src.uuid) -> (dst.parent_uuid, dst.uuid)}

    def print(self):
        self.box_info.print()
        print('  - UUID', self.uuid)
        print('  - Parent UUID', self.parent_uuid)        
        print('  - Node Type', self.node_type)
        for p in self.input_ports:
            p.print()
        for p in self.output_ports:
            p.print()

        children_uuid_dict = {}
        for child in self.children:
            children_uuid_dict[child.uuid] = child
            
        if len(self.connections):
            print('  - Connections:')
        for src, dst in self.connections.items():
            src_box_uuid = src[0]
            dst_box_uuid = dst[0]
            print('    -', children_uuid_dict[src_box_uuid].box_info.name, '->',\
                  children_uuid_dict[dst_box_uuid].box_info.name)            
            
        for child in self.children:
            child.print()
