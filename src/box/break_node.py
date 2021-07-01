import logging


class BreakNode:
    def __init__(self, box, generator):
        self.box = box
        self.generator = generator
        logging.debug("Constructed break node")

    def to_python(self, indent="    "):
        logging.debug("Generating Python for break node")
        return indent + "break\n"
