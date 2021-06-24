class OutputsNode:
    def __init__(self, node_ref, return_vars):
        self.node_ref = node_ref
        self.return_vars = return_vars

    def to_python(self):
        if len(self.return_vars) == 0:
            return "return"
        elif len(self.return_vars) == 1:
            return "return " + str(self.return_vars[0])
        elif len(self.return_vars) > 1:
            result = "return ("
            for i, output in enumerate(self.return_vars):
                result += output
                if i < len(self.return_vars) - 1:
                    result += ", "
                index += 1
            result += ")"
        else:
            return "return"
