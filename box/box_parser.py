from box import Box
from box_iterator import BoxIterator
from box_info import BoxInfo
import box_type
from operator import attrgetter
from port import Port
import uuid

BOX_TOKEN_TOP_LEFT      = '┌'
BOX_TOKEN_TOP_RIGHT     = '┐'
BOX_TOKEN_BOTTOM_LEFT   = '└'
BOX_TOKEN_BOTTOM_RIGHT  = '┘'
BOX_TOKEN_HORIZONTAL    = '─'
BOX_TOKEN_VERTICAL      = '│'
BOX_TOKEN_INPUT_PORT    = '┼' 
BOX_TOKEN_OUTPUT_PORT   = '┼'
BOX_TOKEN_FUNCTION      = 'ƒ'
BOX_TOKEN_COMMENT       = '/*...*/'

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

                            # Parse box contents
                            box_contents = ""
                            i_start = top_left[0]
                            i_end = bottom_right[0]
                            j_start = top_left[1]
                            j_end = top_right[1]
                            i_start += 1
                            j_start += 1

                            while i_start < i_end:
                                while j_start < j_end:
                                    box_contents += lines[i_start][j_start]
                                    j_start += 1
                                box_contents += "\n"
                                i_start += 1
                                j_start = top_left[1] + 1

                            # Create new BoxInfo object for this box
                            boxes.append(BoxInfo(box_name, box_contents,
                                                 top_left, top_right, bottom_right, bottom_left,
                                                 input_ports, output_ports))

    return lines, boxes

def generate_uuid():
    return uuid.uuid4()

def new_box(lines, parent, children):
    parent_box = Box()
    parent_box.box_info = parent
    parent_box.uuid = generate_uuid()

    name = parent_box.box_info.name
    if len(name):
        if name[0] == BOX_TOKEN_FUNCTION:
            parent_box.node_type = box_type.BOX_TYPE_FUNCTION
            assert name[1] == '('
            assert name[len(name) - 1] == ')'
            parent_box.box_info.name = name[2:len(name) - 1]
        elif name == BOX_TOKEN_COMMENT:
            parent_box.node_type = box_type.BOX_TYPE_COMMENT

    # Save input ports
    for p in parent.input_ports:
        port = Port()
        port.port_type = "input"
        port.x = p[0]
        port.y = p[1]
        port.uuid = generate_uuid()
        port.parent_uuid = parent_box.uuid
        parent_box.input_ports.append(port)

    # Save output ports
    for p in parent.output_ports:
        port = Port()
        port.port_type = "output"
        port.x = p[0]
        port.y = p[1]
        port.uuid = generate_uuid()
        port.parent_uuid = parent_box.uuid
        parent_box.output_ports.append(port)

    # Save children
    for child in children:
        child_box = new_box(lines, child, [])
        child_box.parent_uuid = parent_box.uuid
        parent_box.children.append(child_box)

    # Keep a map of all ports
    # {(x, y): box_guid, ...}
    all_input_ports = {}
    all_output_ports = {}
    for child in parent_box.children:
        if len(child.input_ports):
            for port in child.input_ports:
                all_input_ports[(port.x, port.y)] = (port.parent_uuid, port.uuid)
        if len(child.output_ports):
            for port in child.output_ports:
                all_output_ports[(port.x, port.y)] = (port.parent_uuid, port.uuid)

    # Save connections between children
    for child in parent_box.children:
        if len(child.output_ports):
            # this child box has output ports
            # follow any lines drawn from the output port
            # see which other box it reaches
            for port in child.output_ports:
                src_uuid = port.uuid
                src_parent_uuid = port.parent_uuid
                x, y = port.x, port.y
                it = BoxIterator(lines, x, y)

                direction = "right"
                it.right()

                while True:
                    if it.current() == BOX_TOKEN_HORIZONTAL:
                        if direction == "right":
                            # keep going right
                            it.right()
                        elif direction == "left":
                            # keep going left
                            it.left()
                    elif it.current() == BOX_TOKEN_VERTICAL:
                        if direction == "up":
                            # keep going up
                            it.top()
                        elif direction == "down":
                            # keep going down
                            it.bottom()
                    elif it.current() == BOX_TOKEN_TOP_LEFT:
                        if direction == "up":
                            it.right()
                            direction = "right"
                        elif direction == "left":
                            it.bottom()
                            direction = "down"                                                   
                    elif it.current() == BOX_TOKEN_TOP_RIGHT:
                        if direction == "right":
                            it.bottom()
                            direction = "down"
                        elif direction == "up":
                            it.left()
                            direction = "left"
                    elif it.current() == BOX_TOKEN_BOTTOM_RIGHT:
                        if direction == "right":
                            it.top()
                            direction = "up"
                        elif direction == "down":
                            it.left()
                            direction = "left"
                    elif it.current() == BOX_TOKEN_BOTTOM_LEFT:
                        if direction == "left":
                            it.top()
                            direction = "up"
                        elif direction == "down":
                            it.right()
                            direction = "right"
                    else:
                        break
                possibly_new_port = it.pos()
                if possibly_new_port in all_input_ports:
                    dst = all_input_ports[possibly_new_port]
                    dst_parent_uuid = dst[0]                                        
                    dst_uuid = dst[1]

                    # Record the connection between src and destination
                    parent_box.connections[(src_parent_uuid, src_uuid)] = (dst_parent_uuid, dst_uuid)

                else:
                    print("Invalid connection from (" + str(x) + ", " + str(y) + ")")

    return parent_box

        
def build_parse_tree(lines, boxes):
    parent = min(boxes, key=attrgetter('top_left'))
    boxes.remove(parent)
    children = boxes
    return new_box(lines, parent, children)
