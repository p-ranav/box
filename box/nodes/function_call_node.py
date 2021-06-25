class FunctionCallNode:
    def __init__(self, box_ref, name, args):
        self.box_ref = box_ref
        self.name = name
        self.args = args

    def to_python(self):
        result = ""

        # check if function has outputs
        # if so, need to save output of function call
        if len(self.box_ref.output_ports) > 0:
            result += self.name + "_result = "

        # call the function
        result += self.name + "("
        for i, arg in enumerate(self.args):
            result += arg
            if i < len(self.args) - 1:
                result += ", "
        result += ")"
        
        return result
