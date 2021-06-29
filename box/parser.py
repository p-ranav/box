import re
import uuid

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
    BOX_TOKEN_KEYWORD_WHILE_LOOP = '[While Loop]'    
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

        # List of boxes - Starting from the first box
        # and reaching the final box
        self.flow_of_control = self.__find_order_of_operations(self.starting_box, True)

        # {<Box_1>: "Box_1_foobar_result", <Box_2>: "Box_2_baz_result", ...}
        self.temp_results = {}

        self.function_name = ""

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
            self.uuid = uuid.uuid4()

        def uuid_short(self):
            return str(self.uuid)[:8]

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
                        Parser.BOX_TOKEN_KEYWORD_WHILE_LOOP,
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

    def find_destination_connection(self, start_port, direction = "right"):
        it = Parser.BoxIterator(self.lines, start_port)

        # Start navigation
        if direction == "right":
            it.right()
        elif direction == "left":
            it.left()
        else:
            # TODO: report error
            # Not allowed
            pass

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
            elif it.current() == Parser.BOX_TOKEN_INPUT_PORT:
                # Keep going in the direction we were going
                # This indicates lines crossing over each other
                if direction == "left":
                    it.left()
                elif direction == "right":
                    it.right()
                elif direction == "up":
                    it.up()
                elif direction == "down":
                    it.down()
            elif it.current() == Parser.BOX_TOKEN_DATA_FLOW_PORT or\
                 it.current() == Parser.BOX_TOKEN_CONTROL_FLOW_PORT:
                # We've reached the destination
                # Go back left/right by one position to land on the interface
                # and arrest further movement
                if direction == "right":
                    it.left()
                elif direction == "left":
                    it.right()
                break
            else:
                break

        return it.pos()

    def __has_return_boxes(self):
        result = False
        for box in self.boxes:
            is_return = (box.box_header == Parser.BOX_TOKEN_KEYWORD_RETURN)
            if is_return:
                result = True
                break
        return result

    def sanitize_box_contents(self, box_contents):
        box_contents = box_contents.strip()
        box_contents = box_contents.replace(Parser.BOX_TOKEN_DATA_FLOW_PORT, "")
        box_contents = box_contents.replace(Parser.BOX_TOKEN_CONTROL_FLOW_PORT, "")
        box_contents = box_contents.replace(" ", "")
        box_contents = box_contents.replace("\t", "")
        box_contents = box_contents.replace("\n", "")
        return box_contents

    def is_operator(self, box_contents):
        text = self.sanitize_box_contents(box_contents)
        return (text in Parser.OperatorNode.UNARY_OPERATORS or text in Parser.OperatorNode.BINARY_OPERATORS)

    def is_next_box_a_while_loop(self, box):
        result = False
        # Check if the next box is a while loop
        # If so, do not emit any code unless forced
        has_next_box = (
            len(box.output_control_flow_ports) == 1 and
            len(box.output_data_flow_ports) == 1)
        if has_next_box:
            output_data_flow_port = box.output_data_flow_ports[0]
            destination_data_flow_port = self.find_destination_connection(output_data_flow_port, "right")
            if destination_data_flow_port in self.port_box_map:
                destination_data_flow_box = self.port_box_map[destination_data_flow_port]

                output_control_flow_port = box.output_control_flow_ports[0]
                destination_control_flow_port = self.find_destination_connection(output_control_flow_port, "right")
                if destination_control_flow_port in self.port_box_map:
                    destination_control_flow_box = self.port_box_map[destination_control_flow_port]

                    if destination_data_flow_port == destination_control_flow_port:
                
                        is_while_loop = (destination_data_flow_box.box_header == Parser.BOX_TOKEN_KEYWORD_WHILE_LOOP)
                        if is_while_loop:
                            result = True
        return result
    
    def get_output_data_name(self, box, port):
        result = ""

        is_operator = self.is_operator(box.box_contents)
        is_function = (box.box_header.startswith(Parser.BOX_TOKEN_FUNCTION_START))
        is_function_call = is_function and len(box.input_control_flow_ports) == 1
        is_constant_or_variable = (not is_operator) and (box.box_header == "")
        is_for_loop = (box.box_header == Parser.BOX_TOKEN_KEYWORD_FOR_LOOP)
        is_set = (box.box_header == Parser.BOX_TOKEN_KEYWORD_SET)

        if is_function and len(box.input_control_flow_ports) == 0 and len(box.output_control_flow_ports) == 1:
            # This is a function declaration box
            # This box could have multiple parameters
            col_start = box.top_left[1] + 1
            col_end = box.top_right[1]
            row = port[0]

            for col in range(col_start, col_end):
                result += self.lines[row][col]                
                result = self.sanitize_box_contents(result)
        elif is_function_call:
            result = self.temp_results[box]
        elif is_constant_or_variable:
            result = self.sanitize_box_contents(box.box_contents)
        elif is_operator:
            result = self.temp_results[box]
        elif is_for_loop:
            result = self.temp_results[box]
        elif is_set:
            result = self.temp_result[box]

        return result

    class OperatorNode:

        # Arithmetic operators
        OPERATOR_TOKEN_ADD                   = "+"
        OPERATOR_TOKEN_SUBTRACT              = "-"
        OPERATOR_TOKEN_MULTIPLY              = "*"
        OPERATOR_TOKEN_DIVIDE                = "/"
        OPERATOR_TOKEN_MODULO                = "%"
        OPERATOR_TOKEN_EXPONENTIATION        = "**"
        OPERATOR_TOKEN_FLOOR_DIVISION        = "//"                

        # Logical operators
        OPERATOR_TOKEN_AND                   = "&&"
        OPERATOR_TOKEN_OR                    = "||"        
        OPERATOR_TOKEN_NOT                   = "!"

        # Comparison operators
        OPERATOR_TOKEN_GREATER_THAN          = ">"
        OPERATOR_TOKEN_GREATER_THAN_OR_EQUAL = ">="
        OPERATOR_TOKEN_LESS_THAN             = "<"
        OPERATOR_TOKEN_LESS_THAN_OR_EQUAL    = "<="
        OPERATOR_TOKEN_EQUAL                 = "=="
        OPERATOR_TOKEN_NOT_EQUAL             = "!="

        UNARY_OPERATORS = [
            OPERATOR_TOKEN_NOT
        ]

        BINARY_OPERATORS = [
            OPERATOR_TOKEN_ADD, OPERATOR_TOKEN_SUBTRACT,
            OPERATOR_TOKEN_MULTIPLY, OPERATOR_TOKEN_DIVIDE,
            OPERATOR_TOKEN_MODULO, OPERATOR_TOKEN_EXPONENTIATION,
            OPERATOR_TOKEN_FLOOR_DIVISION,

            OPERATOR_TOKEN_AND, OPERATOR_TOKEN_OR,
            OPERATOR_TOKEN_GREATER_THAN, OPERATOR_TOKEN_GREATER_THAN_OR_EQUAL,
            OPERATOR_TOKEN_LESS_THAN, OPERATOR_TOKEN_LESS_THAN_OR_EQUAL,
            OPERATOR_TOKEN_EQUAL, OPERATOR_TOKEN_NOT_EQUAL
            ]
        
        def __init__(self, box, parser):
            self.box = box
            self.parser = parser
            self.__result_prefix = "op"

        def to_python(self, indent = "    ", store_result_in_variable=True, called_by_next_box=False):
            result = ""
            
            # Check number of input ports
            box_contents = self.parser.sanitize_box_contents(self.box.box_contents)

            operator = box_contents

            # Check if the next box is a while loop
            # If so, do not emit any code unless forced
            if self.parser.is_next_box_a_while_loop(self.box):
                if not called_by_next_box:
                    return result

            if operator in Parser.OperatorNode.UNARY_OPERATORS:
                assert(len(self.box.input_data_flow_ports) == 1)

                input_port_0 = self.parser.find_destination_connection(self.box.input_data_flow_ports[0], "left")
                input_box = self.parser.port_box_map[input_port_0]

                argument = self.parser.get_output_data_name(input_box, input_port_0)

                if store_result_in_variable:
                    operator_result = self.__result_prefix + "_" + self.box.uuid_short() + "_result"
                    self.parser.temp_results[self.box] = operator_result                
                    result = indent + operator_result + " = "

                result += "(not " + argument + ")\n"
                
            elif operator in Parser.OperatorNode.BINARY_OPERATORS:
                # There must be exactly 2 input data flow ports for this node
                assert(len(self.box.input_data_flow_ports) == 2)

                input_port_0 = self.parser.find_destination_connection(self.box.input_data_flow_ports[0], "left")
                input_port_1 = self.parser.find_destination_connection(self.box.input_data_flow_ports[1], "left")

                operator_arguments = []
                for i, port in enumerate([input_port_0, input_port_1]):
                    box = self.parser.port_box_map[port]
                    operator_arguments.append(self.parser.get_output_data_name(box, port))
                        
                lhs, rhs = operator_arguments

                # Find the two input boxes and parse their contents
                # Then set result to:
                #   <box_1_contents> <operator> <box_2_contents>
                #
                # Create a variable to store the result
                if store_result_in_variable:
                    operator_result = self.__result_prefix + "_" + self.box.uuid_short() + "_result"
                    self.parser.temp_results[self.box] = operator_result                
                    result = indent + operator_result + " = "
                    
                result += "(" + lhs + " " + operator + " " + rhs + ")\n"

            return result

    class SetNode:
        def __init__(self, box, parser):
            self.box = box
            self.parser = parser

        def to_python(self, indent="    "):
            assert(len(self.box.input_data_flow_ports) == 2)

            input_port_0 = self.parser.find_destination_connection(self.box.input_data_flow_ports[0], "left")
            input_port_1 = self.parser.find_destination_connection(self.box.input_data_flow_ports[1], "left")

            set_arguments = []
            for i, port in enumerate([input_port_0, input_port_1]):
                box = self.parser.port_box_map[port]
                set_arguments.append(self.parser.get_output_data_name(box, port))
                
            lhs, rhs = set_arguments
            
            # Find the two input boxes and parse their contents
            # Then set result to:
            #   <box_1_contents> = <box_2_contents>
            #
            # Create a variable to store the result                
            
            self.parser.temp_results[self.box] = lhs
            
            result = indent + lhs + " = " + rhs + "\n"

            return result

    class BranchNode:
        def __init__(self, box, true_case, false_case, parser):
            self.box = box
            self.true_case = true_case
            self.false_case = false_case
            self.parser = parser

        def to_python(self, indent="    "):
            assert(len(self.box.input_data_flow_ports) == 1)
            input_port = self.parser.find_destination_connection(self.box.input_data_flow_ports[0], "left")
            condition_box = self.parser.port_box_map[input_port]

            # Find temp_results from condition_box
            condition_result_name = self.parser.temp_results[condition_box]

            result = indent + "if " + condition_result_name + " == True:\n"
            for statement in self.true_case:
                result += statement.to_python(indent + "    ")
                
            result += indent + "else:\n"
            for statement in self.false_case:
                result += statement.to_python(indent + "    ")            
            
            return result

    class ForLoopNode:
        def __init__(self, box, loop_body, parser):
            self.box = box
            self.parser = parser
            self.loop_body = loop_body

        def to_python(self, indent="    "):
            result = indent + "for "

            assert(len(self.box.input_data_flow_ports) == 3)

            input_port_0 = self.parser.find_destination_connection(self.box.input_data_flow_ports[0], "left")
            input_port_1 = self.parser.find_destination_connection(self.box.input_data_flow_ports[1], "left")
            input_port_2 = self.parser.find_destination_connection(self.box.input_data_flow_ports[2], "left")            

            loop_arguments = []
            for i, port in enumerate([input_port_0, input_port_1, input_port_2]):
                box = self.parser.port_box_map[port]
                loop_arguments.append(self.parser.get_output_data_name(box, port))
                
            start_index, end_index, step = loop_arguments

            current_index = "index_" + self.box.uuid_short()
            self.parser.temp_results[self.box] = current_index

            result += current_index + " in range(" + start_index + ", " + end_index + ", " + step + "):\n"

            for statement in self.loop_body:
                result += statement.to_python(indent + "    ")
            result += "\n"
            
            return result

    class WhileLoopNode:
        def __init__(self, box, loop_body, parser):
            self.box = box
            self.parser = parser
            self.loop_body = loop_body

        def to_python(self, indent="    "):
            result = indent + "while "

            assert(len(self.box.input_data_flow_ports) == 1) # the while condition

            input_port_0 = self.parser.find_destination_connection(self.box.input_data_flow_ports[0], "left")
            input_box = self.parser.port_box_map[input_port_0]

            # Check if the previous box is either
            # - OperatorNode
            # - FunctionCallNode
            # In these cases,
            # Wrap the previous data flow box and get its emitted python code
            # This is the WhileLoop condition
            is_operator = self.parser.is_operator(input_box.box_contents)
            is_function = (input_box.box_header.startswith(Parser.BOX_TOKEN_FUNCTION_START))
            is_function_call = is_function and len(input_box.input_control_flow_ports) == 1

            condition = ""

            if is_operator or is_function_call:
                condition = self.parser.create_node(input_box).to_python(indent="", store_result_in_variable=False, called_by_next_box=True).strip()
            else:
                condition = self.parser.get_output_data_name(input_box, input_port_0)

            result += condition + ":\n"

            for statement in self.loop_body:
                result += statement.to_python(indent + "    ")
            result += "\n"
            
            return result        

    class ReturnNode:
        def __init__(self, box, parser):
            self.box = box
            self.parser = parser

        def to_python(self, indent="    "):
            result = indent + "return"

            return_vals = []
            
            for port in self.box.input_data_flow_ports:
                input_port = self.parser.find_destination_connection(port, "left")
                input_box = self.parser.port_box_map[input_port]
                return_vals.append(self.parser.get_output_data_name(input_box, input_port))

            for i, val in enumerate(return_vals):
                result += " " + val
                if i < len(return_vals) - 1:
                    result += ", "
            result += "\n"

            return result                     

    class FunctionDeclarationNode:
        def __init__(self, box, parser):
            self.box = box
            self.parser = parser

        def to_python(self, indent="    "):
            # Function signature
            result = "def "
            function_name = self.box.box_header
            function_name = function_name[2:len(function_name) - 1]
            function_name = re.sub('[\W_]', '', function_name)
            result += function_name

            self.parser.function_name = function_name
            
            result += "("
            box_contents = self.box.box_contents.split("\n")
            
            parameters = []
            for line in self.box.box_contents.split("\n"):
                if line.endswith(Parser.BOX_TOKEN_DATA_FLOW_PORT):
                    parameters.append(line[:-1].strip())

            for i, param in enumerate(parameters):
                result += param
                if i < len(parameters) - 1:
                    result += ", "

            result += "):\n"            
            return result

    class FunctionCallNode:
        def __init__(self, box, parser):
            self.box = box
            self.parser = parser
            self.__result_prefix = "fn"

        def to_python(self, indent="    ", store_result_in_variable=True, called_by_next_box=False):
            result = ""

            # Check if the next box is a while loop
            # If so, do not emit any code unless forced
            if self.parser.is_next_box_a_while_loop(self.box):
                if not called_by_next_box:
                    return result
                        
            result = indent

            function_name = self.box.box_header
            function_name = function_name[2:len(function_name) - 1]
 
            function_args = []
            
            for port in self.box.input_data_flow_ports:
                input_port = self.parser.find_destination_connection(port, "left")
                input_box = self.parser.port_box_map[input_port]
                function_args.append(self.parser.get_output_data_name(input_box, input_port))

            # Check if function result is used
            if store_result_in_variable and len(self.box.output_data_flow_ports) > 0:
                fn_result = self.__result_prefix + "_" + self.box.uuid_short() + "_result"
                self.parser.temp_results[self.box] = fn_result            
                result += fn_result + " = "
                
            result += function_name                
            result += "("
            for i, arg in enumerate(function_args):
                result += arg
                if i < len(function_args) - 1:
                    result += ", "

            result += ")\n"
            return result

    def create_node(self, box):
        is_math_operation = (box.box_header == "")
        is_return = (box.box_header == Parser.BOX_TOKEN_KEYWORD_RETURN)
        is_set = (box.box_header == Parser.BOX_TOKEN_KEYWORD_SET)
        is_function = (box.box_header.startswith(Parser.BOX_TOKEN_FUNCTION_START))

        if is_math_operation:
            return Parser.OperatorNode(box, self)
        elif is_return:
            return Parser.ReturnNode(box, self)
        elif is_set:
            return Parser.SetNode(box, self)
        elif is_function and len(box.input_control_flow_ports) == 0 and len(box.output_control_flow_ports) == 1:
            return Parser.FunctionDeclarationNode(box, self)
        elif is_function and len(box.input_control_flow_ports) == 1:
            return Parser.FunctionCallNode(box, self)
        else:
            # TODO: Throw an error
            # Unrecognized box type
            return box

    def __find_order_of_operations(self, start, global_first_box = True):
        result = []
        
        # Start from the starting box
        # Go till there are no more boxes to reach
        # Find connections
        # Find control flow boxes, e.g., `Branch`, `For loop` etc.

        # Save the input box
        result.append(self.create_node(start))            

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
            end_port = self.find_destination_connection(start_port)
            end_box = None

            if end_port in self.port_box_map:
                end_box = self.port_box_map[end_port]
            else:
                return result
            
            # This is the second box
            start = end_box

            while True:
                if len(start.output_control_flow_ports) == 0:
                    # End of control flow
                    result.append(self.create_node(start))
                    return result

                is_math_operation = (start.box_header == "")
                is_branch = (start.box_header == Parser.BOX_TOKEN_KEYWORD_BRANCH)
                is_for_loop = (start.box_header == Parser.BOX_TOKEN_KEYWORD_FOR_LOOP)
                is_while_loop = (start.box_header == Parser.BOX_TOKEN_KEYWORD_WHILE_LOOP)                        
                is_return = (start.box_header == Parser.BOX_TOKEN_KEYWORD_RETURN)
                is_set = (start.box_header == Parser.BOX_TOKEN_KEYWORD_SET)

                if is_math_operation:
                    assert(len(start.output_control_flow_ports) == 1)
                    # save and continue
                    result.append(Parser.OperatorNode(start, self))
                    
                    start_port = start.output_control_flow_ports[0]
                    end_port = self.find_destination_connection(start_port)
                    end_box = self.port_box_map[end_port]
                    start = end_box
                    continue
                elif is_set:
                    assert(len(start.output_control_flow_ports) <= 1)
                    # save and continue
                    result.append(Parser.SetNode(start, self))
                    start_port = start.output_control_flow_ports[0]
                    end_port = self.find_destination_connection(start_port)
                    end_box = self.port_box_map[end_port]
                    start = end_box
                    continue
                elif is_return:
                    assert(len(start.output_control_flow_ports) == 0)
                    # This is the end
                    # Stop here and return
                    result.append(Parser.ReturnNode(start, self))
                    break
                elif is_branch:
                    assert(len(start.output_control_flow_ports) == 2)
                    # Two output control flow ports here
                    # The `True` case, and the `False` case
                    true_output_port = start.output_control_flow_ports[0]
                    false_output_port = start.output_control_flow_ports[1]                

                    true_case_start_port = self.find_destination_connection(true_output_port)
                    false_case_start_port = self.find_destination_connection(false_output_port)

                    true_case_start_box = self.port_box_map[true_case_start_port]
                    false_case_start_box = self.port_box_map[false_case_start_port]

                    true_case_control_flow = self.__find_order_of_operations(true_case_start_box, False)
                    false_case_control_flow = self.__find_order_of_operations(false_case_start_box, False)

                    result.append(Parser.BranchNode(start, true_case_control_flow, false_case_control_flow, self))

                    # Branch Control flow should break this loop since we cannot update `start`
                    break
                elif is_for_loop:
                    assert(len(start.output_control_flow_ports) == 2)
                    # Two output control flow ports here
                    # The `Loop body` case, and the `Completed` case
                    loop_body_output_port = start.output_control_flow_ports[0]
                    completed_output_port = start.output_control_flow_ports[1]

                    loop_body_case_start_port = self.find_destination_connection(loop_body_output_port)
                    completed_case_start_port = self.find_destination_connection(completed_output_port)

                    loop_body_case_start_box = self.port_box_map[loop_body_case_start_port]
                    completed_case_start_box = self.port_box_map[completed_case_start_port]

                    loop_body_case_control_flow = self.__find_order_of_operations(loop_body_case_start_box, False)
                    completed_case_control_flow = self.__find_order_of_operations(completed_case_start_box, False)

                    result.append(Parser.ForLoopNode(start, loop_body_case_control_flow, self))
                    result.extend(completed_case_control_flow)

                    # Branch Control flow should break this loop since we cannot update `start`
                    break
                elif is_while_loop:
                    assert(len(start.output_control_flow_ports) == 2)
                    # Two output control flow ports here
                    # The `Loop body` case, and the `Completed` case
                    loop_body_output_port = start.output_control_flow_ports[0]
                    completed_output_port = start.output_control_flow_ports[1]

                    loop_body_case_start_port = self.find_destination_connection(loop_body_output_port)
                    completed_case_start_port = self.find_destination_connection(completed_output_port)

                    loop_body_case_start_box = self.port_box_map[loop_body_case_start_port]
                    completed_case_start_box = self.port_box_map[completed_case_start_port]

                    loop_body_case_control_flow = self.__find_order_of_operations(loop_body_case_start_box, False)
                    completed_case_control_flow = self.__find_order_of_operations(completed_case_start_box, False)

                    result.append(Parser.WhileLoopNode(start, loop_body_case_control_flow, self))
                    result.extend(completed_case_control_flow)

                    # Branch Control flow should break this loop since we cannot update `start`
                    break
                

        return result

    def to_python(self, eval_args, indent="    "):
        assert(len(self.flow_of_control) > 1)
        first = self.flow_of_control[0]
        assert(type(first) == type(Parser.FunctionDeclarationNode(None, self)))

        result = ""
        result += first.to_python()

        # Now add the function body
        for box in self.flow_of_control[1:]:
            result += box.to_python()

        # If evaluation is required, call the function
        if eval_args is not None:
            has_return = self.__has_return_boxes()
            result += "\n"
            if has_return:
                result += "print("
            result += self.function_name + "("

            for i, arg in enumerate(eval_args):
                result += arg
                if i < len(eval_args) - 1:
                    result += ", "
    
            result += ")"
            if has_return:
                result += ")"
        
        return result
        
