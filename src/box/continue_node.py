import logging


class ContinueNode:
    def __init__(self, box, generator):
        self.box = box
        self.generator = generator
        logging.debug("Constructed continue node")

    def to_python(self, indent="    "):
        logging.debug("Generating Python for continue node")
        return indent + "continue\n"
