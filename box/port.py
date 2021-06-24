import uuid

class Port:
    def __init__(self):
        self.name = ""
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
