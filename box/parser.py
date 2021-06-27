
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
    BOX_TOKEN_LEFT_PAREN         = '('
    BOX_TOKEN_FUNCTION_START     = (BOX_TOKEN_FUNCTION + BOX_TOKEN_LEFT_PAREN)
    BOX_TOKEN_RIGHT_PAREN        = ')'
    BOX_TOKEN_KEYWORD_BRANCH     = '[Branch]'    
    BOX_TOKEN_KEYWORD_FOR_LOOP   = '[For Loop]'
    BOX_TOKEN_KEYWORD_RETURN     = '[Return]'    
    BOX_TOKEN_KEYWORD_SET        = '[Set]'
    BOX_TOKEN_DATA_FLOW_PORT     = '○'
    BOX_TOKEN_CONTROL_FLOW_PORT  = '►'
    
    def __init__(self, path):
        self.path = path
        self.lines = self.__read_into_lines(path)

        # {(x1, y1): <Box_1>, (x2, y2): <Box_2>, ...}
        self.port_box_map = {}

        # [<Box_1>, <Box_2>, ...]
        self.boxes = self.__find_boxes()
        
        # <Box_first> - The box from where control flow starts
        self.starting_box = self.__find_start_of_control_flow()

        self.allowed_number_of_output_control_flow_ports = {
            Parser.BOX_TOKEN_KEYWORD_BRANCH: 2,
            Parser.BOX_TOKEN_KEYWORD_FOR_LOOP: 2,
            Parser.BOX_TOKEN_KEYWORD_RETURN: 0,
            Parser.BOX_TOKEN_KEYWORD_SET: 1
        }

        # List of boxes - Starting from the first box
        # and reaching the final box
        self.flow_of_control = self.__find_order_of_operations(self.starting_box, True)

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

    def __is_valid_box_header(self, header):
        result = False

        if header.startswith(Parser.BOX_TOKEN_FUNCTION):
            if len(header) > 3:
                # 'ƒ' '(' <name> ')'
                if header[1] == Parser.BOX_TOKEN_LEFT_PAREN:
                    if header[len(header) - 1] == Parser.BOX_TOKEN_RIGHT_PAREN:
                        result = True
        elif header in [Parser.BOX_TOKEN_KEYWORD_BRANCH,
                        Parser.BOX_TOKEN_KEYWORD_FOR_LOOP,
                        Parser.BOX_TOKEN_KEYWORD_RETURN,
                        Parser.BOX_TOKEN_KEYWORD_SET]:
            # Valid keyword
            result = True
        return result

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

                if not self.__is_valid_box_header(box_header):
                    # This is not a valid box
                    # TODO: Log a DEBUG error
                    continue                    

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
                            new_box = Parser.Box(box_header, box_contents,
                                                 top_left, top_right, bottom_right, bottom_left,
                                                 list(reversed(input_data_flow_ports)),
                                                 list(reversed(input_control_flow_ports)),
                                                 output_data_flow_ports,
                                                 output_control_flow_ports)

                            # Save ports to a Parser-level map
                            for port in new_box.input_data_flow_ports:
                                self.port_box_map[port] = new_box
                            for port in new_box.input_control_flow_ports:
                                self.port_box_map[port] = new_box
                            for port in new_box.output_data_flow_ports:
                                self.port_box_map[port] = new_box
                            for port in new_box.output_control_flow_ports:
                                self.port_box_map[port] = new_box

                            # Save as a valid box
                            result.append(new_box)

        return result

    def __find_start_of_control_flow(self):
        # Find the box with no input control flow ports
        # and one output control flow port
        result = [box for box in self.boxes
                  if len(box.input_control_flow_ports) == 0
                  and len(box.output_control_flow_ports) == 1]
        if len(result) != 1:
            # TODO: Log a DEBUG error
            pass
        return result[0]

    def __find_destination_connection(self, start_port):
        it = Parser.BoxIterator(self.lines, start_port)

        # Start by going right
        direction = "right"
        it.right()

        while True:
            if it.current() == Parser.BOX_TOKEN_HORIZONTAL:
                if direction == "right":
                    # keep going right
                    it.right()
                elif direction == "left":
                    # keep going left
                    it.left()
            elif it.current() == Parser.BOX_TOKEN_VERTICAL:
                if direction == "up":
                    # keep going up
                    it.up()
                elif direction == "down":
                    # keep going down
                    it.down()
            elif it.current() == Parser.BOX_TOKEN_TOP_LEFT:
                if direction == "up":
                    it.right()
                    direction = "right"
                elif direction == "left":
                    it.down()
                    direction = "down"                                                   
            elif it.current() == Parser.BOX_TOKEN_TOP_RIGHT:
                if direction == "right":
                    it.down()
                    direction = "down"
                elif direction == "up":
                    it.left()
                    direction = "left"
            elif it.current() == Parser.BOX_TOKEN_BOTTOM_RIGHT:
                if direction == "right":
                    it.up()
                    direction = "up"
                elif direction == "down":
                    it.left()
                    direction = "left"
            elif it.current() == Parser.BOX_TOKEN_BOTTOM_LEFT:
                if direction == "left":
                    it.up()
                    direction = "up"
                elif direction == "down":
                    it.right()
                    direction = "right"
            else:
                break

        return it.pos()

    class SimpleOperationControlFlow:
        def __init__(self, box):
            self.box = box

    class SetControlFlow:
        def __init__(self, box):
            self.box = box

    class BranchControlFlow:
        def __init__(self, true_case, false_case):
            self.true_case = true_case
            self.false_case = false_case

    class ForLoopControlFlow:
        def __init__(self, loop_body):
            self.loop_body = loop_body

    class ReturnControlFlow:
        def __init__(self, box):
            self.box = box

    class FunctionDeclarationControlFlow:
        def __init__(self, box):
            self.box = box

    class FunctionCallControlFlow:
        def __init__(self, box):
            self.box = box            

    def __create_control_flow_wrapper(self, box):
        is_math_operation = (box.box_header == "")
        is_return = (box.box_header == Parser.BOX_TOKEN_KEYWORD_RETURN)
        is_set = (box.box_header == Parser.BOX_TOKEN_KEYWORD_SET)
        is_function = (box.box_header.startswith(Parser.BOX_TOKEN_FUNCTION_START))

        if is_math_operation:
            return Parser.SimpleOperationControlFlow(box)
        elif is_return:
            return Parser.ReturnControlFlow(box)
        elif is_set:
            return Parser.SetControlFlow(box)
        elif is_function and len(box.input_control_flow_ports) == 0 and len(box.output_control_flow_ports) == 1:
            return Parser.FunctionDeclarationControlFlow(box)
        elif is_function and len(box.input_control_flow_ports) == 1:
            return Parser.FunctionCallControlFlow(box)
        else:
            return box

    def __find_order_of_operations(self, start, global_first_box = True):
        result = []
        
        # Start from the starting box
        # Go till there are no more boxes to reach
        # Find connections
        # Find control flow boxes, e.g., `Branch`, `For loop` etc.

        # Save the first box
        result.append(self.__create_control_flow_wrapper(start))

        if global_first_box and len(start.output_control_flow_ports) != 1:
            # Possibilities:
            # 1. Too many output control flow ports
            # 2. Zero control flow ports
            return result
        elif len(start.output_control_flow_ports) == 0:
            # In case of `Return` boxes
            # There won't be any output_control_flow_ports
            # Just return early
            return result
        else:
            start_port = start.output_control_flow_ports[0]
            end_port = self.__find_destination_connection(start_port)
            end_box = None
            if end_port in self.port_box_map:
                end_box = self.port_box_map[end_port]
            else:
                return result
            
            # This is the second box
            result.append(self.__create_control_flow_wrapper(end_box))

            start = end_box

            while True:
                # Check if number of output_control_flow_ports is valid for this box
                num_output_control_flow_ports = len(start.output_control_flow_ports)

                if start.box_header in self.allowed_number_of_output_control_flow_ports:
                    if num_output_control_flow_ports != self.allowed_number_of_output_control_flow_ports[start.box_header]:
                        # TODO: Report error and exit
                        break
                else:
                    if num_output_control_flow_ports != 1:
                        # TODO: Report error and exit
                        break

                is_math_operation = (start.box_header == "")
                is_branch = (start.box_header == Parser.BOX_TOKEN_KEYWORD_BRANCH)
                is_for_loop = (start.box_header == Parser.BOX_TOKEN_KEYWORD_FOR_LOOP)
                is_return = (start.box_header == Parser.BOX_TOKEN_KEYWORD_RETURN)
                is_set = (start.box_header == Parser.BOX_TOKEN_KEYWORD_SET)

                if is_math_operation:
                    # save and continue
                    result.append(Parser.SimpleOperationControlFlow(start))
                    start_port = start.output_control_flow_ports[0]
                    end_port = self.__find_destination_connection(start_port)
                    end_box = self.port_box_map[end_port]
                    start = end_box
                    continue
                elif is_set:
                    # save and continue
                    result.append(Parser.SetControlFlow(start))
                    start_port = start.output_control_flow_ports[0]
                    end_port = self.__find_destination_connection(start_port)
                    end_box = self.port_box_map[end_port]
                    start = end_box
                    continue
                elif is_return:
                    # This is the end
                    # Stop here and return
                    result.append(Parser.ReturnControlFlow(start))
                    break
                elif is_branch:
                    # Two output control flow ports here
                    # The `True` case, and the `False` case
                    true_output_port = start.output_control_flow_ports[0]
                    false_output_port = start.output_control_flow_ports[1]                

                    true_case_start_port = self.__find_destination_connection(true_output_port)
                    false_case_start_port = self.__find_destination_connection(false_output_port)

                    true_case_start_box = self.port_box_map[true_case_start_port]
                    false_case_start_box = self.port_box_map[false_case_start_port]

                    true_case_control_flow = self.__find_order_of_operations(true_case_start_box, False)
                    false_case_control_flow = self.__find_order_of_operations(false_case_start_box, False)

                    result.append(Parser.BranchControlFlow(true_case_control_flow, false_case_control_flow))

                    # Branch Control flow should break this loop since we cannot update `start`
                    break
                elif is_for_loop:
                    # Two output control flow ports here
                    # The `Loop body` case, and the `Completed` case
                    loop_body_output_port = start.output_control_flow_ports[0]
                    completed_output_port = start.output_control_flow_ports[1]

                    loop_body_case_start_port = self.__find_destination_connection(loop_body_output_port)
                    completed_case_start_port = self.__find_destination_connection(completed_output_port)

                    loop_body_case_start_box = self.port_box_map[loop_body_case_start_port]
                    completed_case_start_box = self.port_box_map[completed_case_start_port]

                    loop_body_case_control_flow = self.__find_order_of_operations(loop_body_case_start_box, False)
                    completed_case_control_flow = self.__find_order_of_operations(completed_case_start_box, False)

                    result.append(Parser.ForLoopControlFlow(loop_body_case_control_flow))

                    result.extend(completed_case_control_flow)

                    # Branch Control flow should break this loop since we cannot update `start`
                    break

        return result
        