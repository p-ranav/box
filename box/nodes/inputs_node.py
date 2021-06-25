class InputsNode:
    def __init__(self, box_ref):
        self.box_ref = box_ref

    def to_python(self):
        index = 0
        result = "("
        for inp in self.box_ref.output_ports:
            result += "param_" + str(index)
            if index < len(self.box_ref.output_ports) - 1:
                result += ", "
            index += 1
        result += ")"
        return result
