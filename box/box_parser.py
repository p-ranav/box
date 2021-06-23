from box_iterator import BoxIterator
from box_info import BoxInfo

BOX_TOKEN_TOP_LEFT     = '┌'
BOX_TOKEN_TOP_RIGHT    = '┐'
BOX_TOKEN_BOTTOM_LEFT  = '└'
BOX_TOKEN_BOTTOM_RIGHT = '┘'
BOX_TOKEN_HORIZONTAL   = '─'
BOX_TOKEN_VERTICAL     = '│'
BOX_TOKEN_INPUT_PORT   = '┼' 
BOX_TOKEN_OUTPUT_PORT  = '┼' 

def detect_boxes(filename):
    boxes = []
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
        detected_boxes = []
        box_top_left_start = (BOX_TOKEN_TOP_LEFT + BOX_TOKEN_HORIZONTAL)
        for i, line in enumerate(lines):
            row = i                
            if box_top_left_start in line:
                cols = [n for n in range(len(line)) if line.find(box_top_left_start, n) == n]
                for col in cols:
                    detected_boxes.append([row, col])

        # Follow each line and find box dimensions
        for start_of_new_box in detected_boxes:
            box_name = ""
            top_left = (0, 0)
            top_right = (0, 0)
            bottom_left = (0, 0)
            bottom_right = (0, 0)
            input_ports = []
            output_ports = []

            it = BoxIterator(lines, start_of_new_box[0], start_of_new_box[1])

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
                # print("Not top right", it.current(), it.pos())
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
                    # print("Not bottom right", it.current(), it.pos())
                    continue
                else:
                    # We've reached bottom_right
                    bottom_right = it.pos()
                    it.left()
                    while it.current() == BOX_TOKEN_HORIZONTAL:
                        it.left()

                    if it.current() != BOX_TOKEN_BOTTOM_LEFT:
                        # This is not a valid box
                        # print("Not bottom left", it.current())
                        continue
                    else:
                        # We've reached bottom_left
                        bottom_left = it.pos()
                        it.top()
                        while it.current() == BOX_TOKEN_VERTICAL or \
                              it.current() == BOX_TOKEN_INPUT_PORT:
                            if it.current() == BOX_TOKEN_INPUT_PORT:
                                while it.current() == BOX_TOKEN_INPUT_PORT:
                                    input_ports.append(it.pos())
                                    it.top()
                            else:
                                it.top()                            

                        if it.current() != BOX_TOKEN_TOP_LEFT:
                            # This is not a valid box
                            # print("Not top left", it.current(), it.pos())
                            continue
                        else:
                            # This is a valid box
                            boxes.append(BoxInfo(box_name,
                                                 top_left, top_right, bottom_right, bottom_left,
                                                 input_ports, output_ports))

    return boxes
