class FunctionCallNode:
    def __init__(self, node_ref, name, args, save_output = False):
        self.node_ref = node_ref
        self.name = name
        self.args = args
        self.save_output = save_output

    def to_python(self):
        result = ""
        if self.save_output:
            result += self.name + "_result = " 
        result += self.name + "("
        for i, arg in enumerate(self.args):
            result += arg
            if i < len(self.args) - 1:
                result += ", "
        result += ")"
        return result
