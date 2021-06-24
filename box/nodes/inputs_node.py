class InputsNode:
    def __init__(self, node_ref):
        self.node_ref = node_ref

    def to_python(self):
        index = 0
        result = "("
        for inp in self.node_ref.output_ports:
            result += "param_" + str(index)
            if index < len(self.node_ref.output_ports) - 1:
                result += ", "
            index += 1
        result += ")"
        return result
