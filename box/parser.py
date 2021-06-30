import re
import uuid
from box.box import Box
from box.token import Token
from box.box_iterator import BoxIterator
from box.operator_node import OperatorNode
from box.set_node import SetNode
from box.branch_node import BranchNode
from box.for_loop_node import ForLoopNode
from box.while_loop_node import WhileLoopNode
from box.return_node import ReturnNode
from box.function_declaration_node import FunctionDeclarationNode
from box.function_call_node import FunctionCallNode


class Parser:
    def __init__(self, path):
        self.path = path
        self.lines = self._read_into_lines(path)

        # {(x1, y1): <Box_1>, (x2, y2): <Box_2>, ...}
        self.port_box_map = {}

        # [<Box_1>, <Box_2>, ...]
        self.boxes = self._find_boxes()

        # <Box_first> - The box from where control flow starts
        self.starting_box = self._find_start_of_control_flow()

        # List of boxes - Starting from the first box
        # and reaching the final box
        self.flow_of_control = self._find_order_of_operations(self.starting_box, True)

        # {<Box_1>: "Box_1_foobar_result", <Box_2>: "Box_2_baz_result", ...}
        self.temp_results = {}

        self.function_name = ""

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

    def _find_start_of_control_flow(self):
        # Find the box with no input control flow ports
        # and one output control flow port
        result = [
            box
            for box in self.boxes
            if len(box.input_control_flow_ports) == 0
            and len(box.output_control_flow_ports) == 1
        ]
        if len(result) != 1:
            # TODO: Log a DEBUG error
            pass
        return result[0]

    def _find_destination_connection(self, start_port, direction="right"):
        it = BoxIterator(self.lines, start_port)

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
            if it.current() == Token.HORIZONTAL:
                if direction == "right":
                    # keep going right
                    it.right()
                elif direction == "left":
                    # keep going left
                    it.left()
            elif it.current() == Token.VERTICAL:
                if direction == "up":
                    # keep going up
                    it.up()
                elif direction == "down":
                    # keep going down
                    it.down()
            elif it.current() == Token.TOP_LEFT:
                if direction == "up":
                    it.right()
                    direction = "right"
                elif direction == "left":
                    it.down()
                    direction = "down"
            elif it.current() == Token.TOP_RIGHT:
                if direction == "right":
                    it.down()
                    direction = "down"
                elif direction == "up":
                    it.left()
                    direction = "left"
            elif it.current() == Token.BOTTOM_RIGHT:
                if direction == "right":
                    it.up()
                    direction = "up"
                elif direction == "down":
                    it.left()
                    direction = "left"
            elif it.current() == Token.BOTTOM_LEFT:
                if direction == "left":
                    it.up()
                    direction = "up"
                elif direction == "down":
                    it.right()
                    direction = "right"
            elif it.current() == Token.INPUT_PORT:
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
            elif (
                it.current() == Token.DATA_FLOW_PORT
                or it.current() == Token.CONTROL_FLOW_PORT
            ):
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

    def _has_return_boxes(self):
        result = False
        for box in self.boxes:
            is_return = box.box_header == Token.KEYWORD_RETURN
            if is_return:
                result = True
                break
        return result

    def _sanitize_box_contents(self, box_contents):
        box_contents = box_contents.strip()
        box_contents = box_contents.replace(Token.DATA_FLOW_PORT, "")
        box_contents = box_contents.replace(Token.CONTROL_FLOW_PORT, "")
        box_contents = box_contents.replace(" ", "")
        box_contents = box_contents.replace("\t", "")
        box_contents = box_contents.replace("\n", "")
        return box_contents

    def _is_operator(self, box_contents):
        text = self._sanitize_box_contents(box_contents)
        return (
            text in OperatorNode.UNARY_OPERATORS
            or text in OperatorNode.BINARY_OPERATORS
        )

    def _is_next_box_a_while_loop(self, box):
        result = False
        # Check if the next box is a while loop
        # If so, do not emit any code unless forced
        has_next_box = (
            len(box.output_control_flow_ports) == 1
            and len(box.output_data_flow_ports) == 1
        )
        if has_next_box:
            output_data_flow_port = box.output_data_flow_ports[0]
            destination_data_flow_port = self._find_destination_connection(
                output_data_flow_port, "right"
            )
            if destination_data_flow_port in self.port_box_map:
                destination_data_flow_box = self.port_box_map[
                    destination_data_flow_port
                ]

                output_control_flow_port = box.output_control_flow_ports[0]
                destination_control_flow_port = self._find_destination_connection(
                    output_control_flow_port, "right"
                )
                if destination_control_flow_port in self.port_box_map:
                    destination_control_flow_box = self.port_box_map[
                        destination_control_flow_port
                    ]

                    if destination_data_flow_port == destination_control_flow_port:

                        is_while_loop = (
                            destination_data_flow_box.box_header
                            == Token.KEYWORD_WHILE_LOOP
                        )
                        if is_while_loop:
                            result = True
        return result

    def _get_output_data_name(self, box, port):
        result = ""

        is_operator = self._is_operator(box.box_contents)
        is_function = box.box_header.startswith(Token.FUNCTION_START)
        is_function_call = is_function and len(box.input_control_flow_ports) == 1
        is_constant_or_variable = (not is_operator) and (box.box_header == "")
        is_for_loop = box.box_header == Token.KEYWORD_FOR_LOOP
        is_set = box.box_header == Token.KEYWORD_SET

        if (
            is_function
            and len(box.input_control_flow_ports) == 0
            and len(box.output_control_flow_ports) == 1
        ):
            # This is a function declaration box
            # This box could have multiple parameters
            col_start = box.top_left[1] + 1
            col_end = box.top_right[1]
            row = port[0]

            for col in range(col_start, col_end):
                result += self.lines[row][col]
                result = self._sanitize_box_contents(result)
        elif is_function_call:
            result = self.temp_results[box]
        elif is_constant_or_variable:
            result = self._sanitize_box_contents(box.box_contents)
        elif is_operator:
            result = self.temp_results[box]
        elif is_for_loop:
            result = self.temp_results[box]
        elif is_set:
            result = self.temp_result[box]

        return result

    def _create_node(self, box):
        is_math_operation = box.box_header == ""
        is_return = box.box_header == Token.KEYWORD_RETURN
        is_set = box.box_header == Token.KEYWORD_SET
        is_function = box.box_header.startswith(Token.FUNCTION_START)

        if is_math_operation:
            return OperatorNode(box, self)
        elif is_return:
            return ReturnNode(box, self)
        elif is_set:
            return SetNode(box, self)
        elif (
            is_function
            and len(box.input_control_flow_ports) == 0
            and len(box.output_control_flow_ports) == 1
        ):
            return FunctionDeclarationNode(box, self)
        elif is_function and len(box.input_control_flow_ports) == 1:
            return FunctionCallNode(box, self)
        else:
            # TODO: Throw an error
            # Unrecognized box type
            return box

    def _find_order_of_operations(self, start, global_first_box=True):
        result = []

        # Start from the starting box
        # Go till there are no more boxes to reach
        # Find connections
        # Find control flow boxes, e.g., `Branch`, `For loop` etc.

        # Save the input box
        result.append(self._create_node(start))

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
            end_port = self._find_destination_connection(start_port)
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
                    result.append(self._create_node(start))
                    return result

                is_math_operation = start.box_header == ""
                is_function = start.box_header.startswith(Token.FUNCTION_START)
                is_function_call = (
                    is_function and len(start.input_control_flow_ports) == 1
                )
                is_branch = start.box_header == Token.KEYWORD_BRANCH
                is_for_loop = start.box_header == Token.KEYWORD_FOR_LOOP
                is_while_loop = start.box_header == Token.KEYWORD_WHILE_LOOP
                is_return = start.box_header == Token.KEYWORD_RETURN
                is_set = start.box_header == Token.KEYWORD_SET

                if is_math_operation:
                    assert len(start.output_control_flow_ports) == 1
                    # save and continue
                    result.append(OperatorNode(start, self))

                    start_port = start.output_control_flow_ports[0]
                    end_port = self._find_destination_connection(start_port)
                    end_box = self.port_box_map[end_port]
                    start = end_box
                    continue
                elif is_set:
                    assert len(start.output_control_flow_ports) <= 1
                    # save and continue
                    result.append(SetNode(start, self))

                    if len(start.output_control_flow_ports) > 0:
                        start_port = start.output_control_flow_ports[0]
                        end_port = self._find_destination_connection(start_port)
                        end_box = self.port_box_map[end_port]
                        start = end_box
                        continue
                    else:
                        break
                elif is_return:
                    assert len(start.output_control_flow_ports) == 0
                    # This is the end
                    # Stop here and return
                    result.append(ReturnNode(start, self))
                    break
                elif is_branch:
                    assert len(start.output_control_flow_ports) == 2
                    # Two output control flow ports here
                    # The `True` case, and the `False` case
                    true_output_port = start.output_control_flow_ports[0]
                    false_output_port = start.output_control_flow_ports[1]

                    true_case_start_port = self._find_destination_connection(
                        true_output_port
                    )
                    false_case_start_port = self._find_destination_connection(
                        false_output_port
                    )

                    true_case_start_box = self.port_box_map[true_case_start_port]
                    false_case_start_box = self.port_box_map[false_case_start_port]

                    true_case_control_flow = self._find_order_of_operations(
                        true_case_start_box, False
                    )
                    false_case_control_flow = self._find_order_of_operations(
                        false_case_start_box, False
                    )

                    result.append(
                        BranchNode(
                            start, true_case_control_flow, false_case_control_flow, self
                        )
                    )

                    # Branch Control flow should break this loop since we cannot update `start`
                    break
                elif is_for_loop:
                    assert len(start.output_control_flow_ports) == 2
                    # Two output control flow ports here
                    # The `Loop body` case, and the `Completed` case
                    loop_body_output_port = start.output_control_flow_ports[0]
                    completed_output_port = start.output_control_flow_ports[1]

                    loop_body_case_start_port = self._find_destination_connection(
                        loop_body_output_port
                    )
                    completed_case_start_port = self._find_destination_connection(
                        completed_output_port
                    )

                    loop_body_case_start_box = self.port_box_map[
                        loop_body_case_start_port
                    ]
                    completed_case_start_box = self.port_box_map[
                        completed_case_start_port
                    ]

                    loop_body_case_control_flow = self._find_order_of_operations(
                        loop_body_case_start_box, False
                    )
                    completed_case_control_flow = self._find_order_of_operations(
                        completed_case_start_box, False
                    )

                    result.append(ForLoopNode(start, loop_body_case_control_flow, self))
                    result.extend(completed_case_control_flow)

                    # Branch Control flow should break this loop since we cannot update `start`
                    break
                elif is_while_loop:
                    assert len(start.output_control_flow_ports) == 2
                    # Two output control flow ports here
                    # The `Loop body` case, and the `Completed` case
                    loop_body_output_port = start.output_control_flow_ports[0]
                    completed_output_port = start.output_control_flow_ports[1]

                    loop_body_case_start_port = self._find_destination_connection(
                        loop_body_output_port
                    )
                    completed_case_start_port = self._find_destination_connection(
                        completed_output_port
                    )

                    loop_body_case_start_box = self.port_box_map[
                        loop_body_case_start_port
                    ]
                    completed_case_start_box = self.port_box_map[
                        completed_case_start_port
                    ]

                    loop_body_case_control_flow = self._find_order_of_operations(
                        loop_body_case_start_box, False
                    )
                    completed_case_control_flow = self._find_order_of_operations(
                        completed_case_start_box, False
                    )

                    result.append(
                        WhileLoopNode(start, loop_body_case_control_flow, self)
                    )
                    result.extend(completed_case_control_flow)

                    # Branch Control flow should break this loop since we cannot update `start`
                    break

                elif is_function_call:
                    assert len(start.output_control_flow_ports) <= 1

                    # save and continue
                    result.append(FunctionCallNode(start, self))

                    if len(start.output_control_flow_ports) > 0:
                        start_port = start.output_control_flow_ports[0]
                        end_port = self._find_destination_connection(start_port)
                        end_box = self.port_box_map[end_port]
                        start = end_box
                        continue
                    else:
                        break

        return result

    def to_python(self, eval_args, indent="    "):
        assert len(self.flow_of_control) > 1
        first = self.flow_of_control[0]
        assert type(first) == type(FunctionDeclarationNode(None, self))

        result = ""
        result += first.to_python()

        # Now add the function body
        for box in self.flow_of_control[1:]:
            result += box.to_python()

        # If evaluation is required, call the function
        if eval_args is not None:
            has_return = self._has_return_boxes()
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
