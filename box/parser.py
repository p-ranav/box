
class Parser:
    BOX_TOKEN_TOP_LEFT           = '┌'
    BOX_TOKEN_TOP_RIGHT          = '┐'
    BOX_TOKEN_BOTTOM_LEFT        = '└'
    BOX_TOKEN_BOTTOM_RIGHT       = '┘'
    BOX_TOKEN_HORIZONTAL         = '─'
    BOX_TOKEN_BOX_START          = (BOX_TOKEN_TOP_LEFT + BOX_TOKEN_HORIZONTAL)
    BOX_TOKEN_VERTICAL           = '│'
    BOX_TOKEN_INPUT_PORT         = '┼' 
    BOX_TOKEN_OUTPUT_PORT        = '┼'
    BOX_TOKEN_FUNCTION           = 'ƒ'
    BOX_TOKEN_COMMENT            = '/*...*/'
    BOX_TOKEN_SINGLE_QUOTE       = '\''
    BOX_TOKEN_DOUBLE_QUOTE       = '"'
    BOX_TOKEN_OPEN_PAREN         = '('
    BOX_TOKEN_CLOSE_PAREN        = ')'
    BOX_TOKEN_KEYWORD_BRANCH     = '[Branch]'    
    BOX_TOKEN_KEYWORD_FOR_LOOP   = '[For Loop]'
    BOX_TOKEN_KEYWORD_RETURN     = '[Return]'    
    BOX_TOKEN_KEYWORD_SET        = '[Set]'    
    BOX_TOKEN_DATA_FLOW_PORT     = '○'
    BOX_TOKEN_CONTROL_FLOW_PORT  = '►'
    
    def __init__(self, path):
        self.path = path
        self.lines = self.__read_into_lines(path)
        self.boxes = self.__find_boxes()

    def __read_into_lines(self, path):
        lines = []
        with open(path, 'r') as file:
            lines = file.readlines()
        
        # Find if there needs to be any padding
        # If so, pad some lines with empty spaces
        result = []
        max_width = max([len(line) for line in lines])
        for line in lines:
            if len(line) < max_width:
                line += " " * (max_width - len(line))
            result.append(line)

        return result

    def __find_potential_boxes(self):
        detected_boxes = []
        for i, line in enumerate(self.lines):
            row = i
            token = Parser.BOX_TOKEN_BOX_START
            if token in line:
                cols = [n for n in range(len(line)) if line.find(token, n) == n]
                for col in cols:
                    detected_boxes.append([row, col])
        return detected_boxes

    class Box:
        def __init__(self, box_header, box_contents,
                     top_left, top_right, bottom_right, bottom_left,
                     input_data_flow_ports, input_control_flow_ports,
                     output_data_flow_ports, output_control_flow_ports):
            self.box_header = box_header
            self.box_contents = box_contents
            self.top_left = top_left
            self.top_right = top_right
            self.bottom_right = bottom_right
            self.bottom_left = bottom_left
            self.input_data_flow_ports = input_data_flow_ports
            self.input_control_flow_ports = input_control_flow_ports
            self.output_data_flow_ports = output_data_flow_ports
            self.output_control_flow_ports = output_control_flow_ports

    class BoxIterator:
        # Class with functions to enable navigating around a box
        def __init__(self, lines, begin_xy):
            self.lines = lines
            self.current_x = begin_xy[0]
            self.current_y = begin_xy[1]

        def current(self):
            if self.current_x < len(self.lines):
                if self.current_y < len(self.lines[self.current_x]):
                    return self.lines[self.current_x][self.current_y]
            return None

        def current_left(self):
            if self.current_x < len(self.lines):
                if self.current_y >= 1 and (self.current_y - 1) < len(self.lines[self.current_x]):
                    return self.lines[self.current_x][self.current_y - 1]
            return None

        def current_right(self):
            if self.current_x < len(self.lines):
                if (self.current_y + 1) < len(self.lines[self.current_x]):
                    return self.lines[self.current_x][self.current_y + 1]
            return None        

        def right(self):
            self.current_y += 1

        def left(self):
            self.current_y -= 1

        def up(self):
            self.current_x -= 1

        def down(self):
            self.current_x += 1

        def pos(self):
            return (self.current_x, self.current_y)

    def __find_boxes(self):
        # Find valid boxes in the input file
        potential_boxes = self.__find_potential_boxes()

        result = []

        for start_of_new_box in potential_boxes:
            box_header = ""
            top_left = start_of_new_box
            top_right = (0, 0)
            bottom_left = (0, 0)
            bottom_right = (0, 0)
            input_data_flow_ports = []
            input_control_flow_ports = []
            output_data_flow_ports = []
            output_control_flow_ports = []

            it = Parser.BoxIterator(self.lines, top_left)

            # Start moving right
            it.right()
            while it.current() == Parser.BOX_TOKEN_HORIZONTAL:
                it.right()

            # Read box header if one exists
            if it.current() != Parser.BOX_TOKEN_HORIZONTAL and\
               it.current() != Parser.BOX_TOKEN_TOP_RIGHT:
                while it.current() and it.current() != Parser.BOX_TOKEN_HORIZONTAL:
                    box_header += it.current()
                    it.right()

            while it.current() == Parser.BOX_TOKEN_HORIZONTAL:
                it.right()

            # Now we should be in BOX_TOKEN_TOP_RIGHT
            if it.current() != Parser.BOX_TOKEN_TOP_RIGHT:
                # This is not a valid box
                # TODO: Log a DEBUG error
                continue
            else:
                # We've reached top right
                top_right = it.pos()

                # time to go down
                it.down()

                # could encounter output ports (data_flow or control_flow ports)
                while it.current() and (it.current() == Parser.BOX_TOKEN_VERTICAL or
                                        it.current() == Parser.BOX_TOKEN_OUTPUT_PORT):
                    if it.current() == Parser.BOX_TOKEN_OUTPUT_PORT:
                        while it.current() == Parser.BOX_TOKEN_OUTPUT_PORT:
                            # Check if data_flow or control_flow port
                            if it.current_left() == Parser.BOX_TOKEN_DATA_FLOW_PORT:
                                # This is a data_flow output port
                                output_data_flow_ports.append(it.pos())
                                it.down()
                            elif it.current_left() == Parser.BOX_TOKEN_CONTROL_FLOW_PORT:
                                # This is a control_flow output port
                                output_control_flow_ports.append(it.pos())
                                it.down()
                            else:
                                # Well this is not a valid port, therefore not a valid box
                                # TODO: Log a DEBUG error
                                break
                    else:
                        it.down()

                if it.current() != Parser.BOX_TOKEN_BOTTOM_RIGHT:
                    # This is not a valid box
                    # TODO: Log a DEBUG error
                    continue
                else:
                    # We've reached the bottom right
                    bottom_right = it.pos()

                    # time to go left
                    it.left()
                    while it.current() == Parser.BOX_TOKEN_HORIZONTAL:
                        it.left()

                    if it.current() != Parser.BOX_TOKEN_BOTTOM_LEFT:
                        # This is not a valid box
                        # TODO: Log a DEBUG error
                        continue
                    else:
                        # We've reached the bottom left
                        bottom_left = it.pos()

                        # time to go up
                        it.up()

                        # could encounter input ports (data_flow or control_flow ports)
                        while it.current() and (it.current() == Parser.BOX_TOKEN_VERTICAL or
                                                it.current() == Parser.BOX_TOKEN_INPUT_PORT):
                            if it.current() == Parser.BOX_TOKEN_INPUT_PORT:
                                # Check if data_flow or control_flow port
                                if it.current_right() == Parser.BOX_TOKEN_DATA_FLOW_PORT:
                                    # This is a data_flow output port
                                    input_data_flow_ports.append(it.pos())
                                    it.up()
                                elif it.current_right() == Parser.BOX_TOKEN_CONTROL_FLOW_PORT:
                                    # This is a control_flow output port
                                    input_control_flow_ports.append(it.pos())
                                    it.up()
                                else:
                                    # Well this is not a valid port, therefore not a valid box
                                    # TODO: Log a DEBUG error
                                    break
                            else:
                                it.up()

                        if it.current() != Parser.BOX_TOKEN_TOP_LEFT:
                            # This is not a valid box
                            # TODO: Log a DEBUG error
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
                                    box_contents += self.lines[i_start][j_start]
                                    j_start += 1
                                box_contents += "\n"
                                i_start += 1
                                j_start = top_left[1] + 1
                            

                            # Save the box meta
                            result.append(Parser.Box(box_header, box_contents,
                                                     top_left, top_right, bottom_right, bottom_left,
                                                     reversed(input_data_flow_ports),
                                                     reversed(input_control_flow_ports),
                                                     output_data_flow_ports,
                                                     output_control_flow_ports))

        return result
