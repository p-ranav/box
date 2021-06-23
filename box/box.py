import os
import sys

BOX_TOKEN_TOP_LEFT     = '┌'
BOX_TOKEN_TOP_RIGHT    = '┐'
BOX_TOKEN_BOTTOM_LEFT  = '└'
BOX_TOKEN_BOTTOM_RIGHT = '┘'
BOX_TOKEN_HORIZONTAL   = '─'
BOX_TOKEN_VERTICAL     = '│'
BOX_TOKEN_INPUT_PORT   = '┼' 
BOX_TOKEN_OUTPUT_PORT  = '┼' 

class BoxInfo:
    def __init__(self, name, top_left, top_right, bottom_right, bottom_left, input_ports, output_ports):
        self.name = name
        # Box dimensions
        self.top_left = top_left
        self.top_right = top_right
        self.bottom_left = bottom_left
        self.bottom_right = bottom_right
        # Box ports
        self.input_ports = input_ports
        self.output_ports = output_ports

    def print(self):
        print("*", self.name)
        print("  - Top left     ", self.top_left)
        print("  - Top right    ", self.top_right)
        print("  - Bottom right ", self.bottom_right)
        print("  - Bottom left  ", self.bottom_left)
        print("  - Input ports  ", self.input_ports)
        print("  - Output ports ", self.output_ports)

def read_file(filename):
    with open(filename) as file:

        # Build a list of lines
        lines = [line for line in file]

        # Find if there needs to be any padding
        # If so, pad some lines with empty spaces
        max_width = max([len(line) for line in lines])
        height = len(lines)
        for line in lines:
            if max_width > len(line):
                line += " "*(max_width - len(line))

        # Find all lines where a box starts
        lines_with_box_starts = []
        box_top_left_start = (BOX_TOKEN_TOP_LEFT + BOX_TOKEN_HORIZONTAL)
        print("Searching for", box_top_left_start)
        for i, line in enumerate(lines):
            row = i                
            if box_top_left_start in line:
                cols = [n for n in range(len(line)) if line.find(box_top_left_start, n) == n]
                print(row, cols)
                for col in cols:
                    print("Found", (row, col), lines[row][col] + lines[row][col + 1] + lines[row][col + 2])
                    lines_with_box_starts.append([row, col])

        class BoxIterator:
            def __init__(self, lines, current_x, current_y):
                self.lines = lines
                self.current_x = current_x
                self.current_y = current_y

            def current(self):
                if self.current_x < len(lines):
                    if self.current_y < len(lines[self.current_x]):
                        return lines[self.current_x][self.current_y]
                return None

            def right(self):
                self.current_y += 1

            def left(self):
                self.current_y -= 1

            def top(self):
                self.current_x -= 1

            def bottom(self):
                self.current_x += 1

            def pos(self):
                return (self.current_x, self.current_y)

        boxes = []
        # follow each line and find box dimensions
        for start in lines_with_box_starts:
            print("Checking with start", start)
            box_name = ""
            top_left = (0, 0)
            top_right = (0, 0)
            bottom_left = (0, 0)
            bottom_right = (0, 0)
            input_ports = []
            output_ports = []

            it = BoxIterator(lines, start[0], start[1])

            top_left = it.pos()

            it.right()
            while it.current() == BOX_TOKEN_HORIZONTAL:
                it.right()

            # Read box name
            while it.current() and it.current() != BOX_TOKEN_HORIZONTAL:
                box_name += it.current()
                it.right()

            while it.current() == BOX_TOKEN_HORIZONTAL:
                it.right()                

            if it.current() != BOX_TOKEN_TOP_RIGHT:
                # This is not a valid box
                print("Not top right", it.current(), it.pos())
                continue
            else:
                # We've reached top_right
                top_right = it.pos()
                
                it.bottom()
                while it.current() == BOX_TOKEN_VERTICAL or it.current() == BOX_TOKEN_OUTPUT_PORT:
                    if it.current() == BOX_TOKEN_OUTPUT_PORT:
                        while it.current() == BOX_TOKEN_OUTPUT_PORT:
                            output_ports.append(it.pos())
                            it.bottom()
                    else:
                        it.bottom()

                if it.current() != BOX_TOKEN_BOTTOM_RIGHT:
                    # This is not a valid box
                    print("Not bottom right", it.current(), it.pos())
                    pass
                else:
                    # We've reached bottom_right
                    bottom_right = it.pos()
                    it.left()
                    while it.current() == BOX_TOKEN_HORIZONTAL:
                        it.left()

                    if it.current() != BOX_TOKEN_BOTTOM_LEFT:
                        # This is not a valid box
                        print("Not bottom left", it.current())
                        continue
                    else:
                        # We've reached bottom_left
                        bottom_left = it.pos()
                        it.top()
                        while it.current() == BOX_TOKEN_VERTICAL or it.current() == BOX_TOKEN_INPUT_PORT:
                            if it.current() == BOX_TOKEN_INPUT_PORT:
                                while it.current() == BOX_TOKEN_INPUT_PORT:
                                    input_ports.append(it.pos())
                                    it.top()
                            else:
                                it.top()                            

                        if it.current() != BOX_TOKEN_TOP_LEFT:
                            # This is not a valid box
                            print("Not top left", it.current(), it.pos())
                            continue
                        else:
                            # This is a valid box
                            boxes.append(BoxInfo(box_name, top_left, top_right, bottom_right, bottom_left, input_ports, output_ports))

        for box in boxes:
            box.print()

def main(filename = "test.box"):
    read_file(filename)
        
if __name__ == "__main__":
    main()
