import re
import uuid
from box.box import Box
from box.token import Token
from box.box_iterator import BoxIterator

class Parser:
    def __init__(self, path):
        self.path = path
        self.lines = self._read_into_lines(path)

        # {(x1, y1): <Box_1>, (x2, y2): <Box_2>, ...}
        self.port_box_map = {}        
                
        # [<Box_1>, <Box_2>, ...]
        self.boxes = self._find_boxes()

    def _read_into_lines(self, path):
        lines = []
        with open(path, "r") as file:
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

    def _find_potential_boxes(self):
        detected_boxes = []
        for i, line in enumerate(self.lines):
            row = i
            token = Token.BOX_START
            if token in line:
                cols = [n for n in range(len(line)) if line.find(token, n) == n]
                for col in cols:
                    detected_boxes.append([row, col])
        return detected_boxes

    def _is_valid_box_header(self, header):
        result = False

        if header.startswith(Token.FUNCTION):
            if len(header) > 3:
                # 'ƒ' '(' <name> ')'
                if header[1] == Token.LEFT_PAREN:
                    if header[len(header) - 1] == Token.RIGHT_PAREN:
                        result = True
        elif header in [
            Token.KEYWORD_BRANCH,
            Token.KEYWORD_FOR_LOOP,
            Token.KEYWORD_WHILE_LOOP,
            Token.KEYWORD_RETURN,
            Token.KEYWORD_SET,
        ]:
            # Valid keyword
            result = True
        return result

    def _find_boxes(self):
        # Find valid boxes in the input file
        potential_boxes = self._find_potential_boxes()

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

            it = BoxIterator(self.lines, top_left)

            # Start moving right
            it.right()
            while it.current() == Token.HORIZONTAL:
                it.right()

            # Read box header if one exists
            if it.current() != Token.HORIZONTAL and it.current() != Token.TOP_RIGHT:
                while it.current() and it.current() != Token.HORIZONTAL:
                    box_header += it.current()
                    it.right()

                if not self._is_valid_box_header(box_header):
                    # This is not a valid box
                    # TODO: Log a DEBUG error
                    continue

            while it.current() == Token.HORIZONTAL:
                it.right()

            # Now we should be in BOX_TOKEN_TOP_RIGHT
            if it.current() != Token.TOP_RIGHT:
                # This is not a valid box
                # TODO: Log a DEBUG error
                continue
            else:
                # We've reached top right
                top_right = it.pos()

                # time to go down
                it.down()

                # could encounter output ports (data_flow or control_flow ports)
                while it.current() and (
                    it.current() == Token.VERTICAL or it.current() == Token.OUTPUT_PORT
                ):
                    if it.current() == Token.OUTPUT_PORT:
                        while it.current() == Token.OUTPUT_PORT:
                            # Check if data_flow or control_flow port
                            if it.current_left() == Token.DATA_FLOW_PORT:
                                # This is a data_flow output port
                                output_data_flow_ports.append(it.pos())
                                it.down()
                            elif it.current_left() == Token.CONTROL_FLOW_PORT:
                                # This is a control_flow output port
                                output_control_flow_ports.append(it.pos())
                                it.down()
                            else:
                                # Well this is not a valid port, therefore not a valid box
                                # TODO: Log a DEBUG error
                                break
                    else:
                        it.down()

                if it.current() != Token.BOTTOM_RIGHT:
                    # This is not a valid box
                    # TODO: Log a DEBUG error
                    continue
                else:
                    # We've reached the bottom right
                    bottom_right = it.pos()

                    # time to go left
                    it.left()
                    while it.current() == Token.HORIZONTAL:
                        it.left()

                    if it.current() != Token.BOTTOM_LEFT:
                        # This is not a valid box
                        # TODO: Log a DEBUG error
                        continue
                    else:
                        # We've reached the bottom left
                        bottom_left = it.pos()

                        # time to go up
                        it.up()

                        # could encounter input ports (data_flow or control_flow ports)
                        while it.current() and (
                            it.current() == Token.VERTICAL
                            or it.current() == Token.INPUT_PORT
                        ):
                            if it.current() == Token.INPUT_PORT:
                                # Check if data_flow or control_flow port
                                if it.current_right() == Token.DATA_FLOW_PORT:
                                    # This is a data_flow output port
                                    input_data_flow_ports.append(it.pos())
                                    it.up()
                                elif it.current_right() == Token.CONTROL_FLOW_PORT:
                                    # This is a control_flow output port
                                    input_control_flow_ports.append(it.pos())
                                    it.up()
                                else:
                                    # Well this is not a valid port, therefore not a valid box
                                    # TODO: Log a DEBUG error
                                    break
                            else:
                                it.up()

                        if it.current() != Token.TOP_LEFT:
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
                            new_box = Box(
                                box_header,
                                box_contents,
                                top_left,
                                top_right,
                                bottom_right,
                                bottom_left,
                                list(reversed(input_data_flow_ports)),
                                list(reversed(input_control_flow_ports)),
                                output_data_flow_ports,
                                output_control_flow_ports,
                            )

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
