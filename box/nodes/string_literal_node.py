class StringLiteralNode:
    def __init__(self, node_ref, name, value):
        self.node_ref = node_ref
        self.name = name
        self.value = value

    def to_python(self):
        return self.name + ' = ' + str(self.value)
