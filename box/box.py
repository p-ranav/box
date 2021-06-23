from operator import attrgetter
from box_info import BoxInfo
import uuid

def generate_uuid():
    return uuid.uuid4()

class Port:
    def __init__(self):
        self.port_type = ""
        self.x = 0
        self.y = 0
        self.uuid = None
        self.parent_uuid = None

    def print(self):
        print('  * Port:')
        print('    - type:', self.port_type)
        print('    - x:', self.x)
        print('    - y:', self.y)
        print('    - UUID:', self.uuid)
        print('    - parent_uuid:', self.parent_uuid)

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

    def print(self):
        self.box_info.print()
        print('  - UUID', self.uuid)
        print('  - Parent UUID', self.parent_uuid)        
        print('  - Node Type', self.node_type)
        for p in self.input_ports:
            p.print()
        for p in self.output_ports:
            p.print()
        for child in self.children:
            child.print()

def new_box(parent, children):
    parent_box = Box()
    parent_box.box_info = parent
    parent_box.uuid = generate_uuid()
    
    for p in parent.input_ports:
        port = Port()
        port.port_type = "input"
        port.x = p[0]
        port.y = p[1]
        port.uuid = generate_uuid()
        port.parent_uuid = parent_box.uuid
        parent_box.input_ports.append(port)

    for p in parent.output_ports:
        port = Port()
        port.port_type = "output"
        port.x = p[0]
        port.y = p[1]
        port.uuid = generate_uuid()
        port.parent_uuid = parent_box.uuid
        parent_box.output_ports.append(port)

    for child in children:
        child_box = new_box(child, [])
        child_box.parent_uuid = parent_box.uuid
        parent_box.children.append(child_box)

    return parent_box

        
def build_parse_tree(box_infos):
    parent = min(box_infos, key=attrgetter('top_left'))
    box_infos.remove(parent)
    children = box_infos

    return new_box(parent, children)
