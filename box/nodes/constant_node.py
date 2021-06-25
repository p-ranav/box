class ConstantNode:
    def __init__(self, box_ref, name, value):
        self.box_ref = box_ref
        self.name = name
        self.value = value
        self.value_type = ""

    def to_python(self):
        return self.name + ' = ' + str(self.value)
