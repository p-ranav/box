
class BoxInfo:
    def __init__(self, name,
                 contents,
                 top_left,
                 top_right,
                 bottom_right,
                 bottom_left,
                 input_ports,
                 output_ports):
        self.name = name
        self.contents = contents
        # Box dimensions
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right
        # Box ports
        self.input_ports = input_ports    # ordered bottom to top
        self.output_ports = output_ports  # ordered top to bottom

    def print(self):
        print("*", self.name)
        print("  - Top left     ", self.top_left)
        print("  - Top right    ", self.top_right)
        print("  - Bottom right ", self.bottom_right)
        print("  - Bottom left  ", self.bottom_left)
        print("  - Input ports  ", self.input_ports)
        print("  - Output ports ", self.output_ports)
