class ContinueNode:
    def __init__(self, box, generator):
        self.box = box
        self.generator = generator

    def to_python(self, indent="    "):
        return indent + "continue\n"
