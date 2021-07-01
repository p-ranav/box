from box.token import Token
from box.box_iterator import BoxIterator
from box.operator_node import OperatorNode
from box.set_node import SetNode
from box.branch_node import BranchNode
from box.for_loop_node import ForLoopNode
from box.for_each_node import ForEachNode
from box.while_loop_node import WhileLoopNode
from box.return_node import ReturnNode
from box.function_declaration_node import FunctionDeclarationNode
from box.function_call_node import FunctionCallNode
from box.break_node import BreakNode
from box.continue_node import ContinueNode


class Generator:
    def __init__(self, parser):
        self.lines = parser.lines
        self.boxes = parser.boxes
        self.port_box_map = parser.port_box_map

        # <Box_first> - The box from where control flow starts
        self.starting_box = self._find_start_of_control_flow()

        # List of boxes - Starting from the first box
        # and reaching the final box
        self.flow_of_control = self._find_order_of_operations(self.starting_box, True)

        # {<Box_1>: "Box_1_foobar_result", <Box_2>: "Box_2_baz_result", ...}
        self.temp_results = {}

        self.function_name = ""

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
            or text in OperatorNode.INCREMENT_DECREMENT_OPERATORS
            or text in OperatorNode.ASSIGNMENT_OPERATORS
        )

    def _get_output_data_name(self, box, port):
        result = ""

        is_operator = self._is_operator(box.box_contents)
        is_function = (
            box.box_header.startswith(Token.FUNCTION_START)
            and len(box.input_control_flow_ports) == 0
            and len(box.output_control_flow_ports) == 1
        )
        is_function_call = (
            box.box_header.startswith(Token.FUNCTION_START)
            and len(box.input_control_flow_ports) <= 1
            and len(box.output_control_flow_ports) <= 1
        )
        is_constant_or_variable = (not is_operator) and (box.box_header == "")
        is_for_loop = box.box_header == Token.KEYWORD_FOR_LOOP
        is_for_each = box.box_header == Token.KEYWORD_FOR_EACH
        is_set = box.box_header == Token.KEYWORD_SET

        if is_function:
            # This is a function declaration box
            # This box could have multiple parameters
            col_start = box.top_left[1] + 1
            col_end = box.top_right[1]
            row = port[0]

            for col in range(col_start, col_end):
                result += self.lines[row][col]
                result = self._sanitize_box_contents(result)
        elif is_function_call:
            if box in self.temp_results:
                result = self.temp_results[box]
            else:
                # Function result is not stored as a temp result
                # Just embed the function call expression in place
                node = self._create_node(box)
                result = node.to_python(
                    "", store_result_in_variable=False, called_by_next_box=True
                ).strip()
        elif is_constant_or_variable:
            result = self._sanitize_box_contents(box.box_contents)
        elif is_operator:
            if box in self.temp_results:
                result = self.temp_results[box]
            else:
                # No temp result, just embed the expression in place
                node = self._create_node(box)
                result = node.to_python(
                    "", store_result_in_variable=False, called_by_next_box=True
                ).strip()
        elif is_for_loop or is_for_each:
            if box in self.temp_results:
                result = self.temp_results[box]
            else:
                # TODO: report error
                pass
        elif is_set:
            if box in self.temp_results:
                result = self.temp_result[box]
            else:
                # TODO: report error
                pass

        return result

    def _create_node(self, box):        
        is_math_operation = box.box_header == ""
        is_return = box.box_header == Token.KEYWORD_RETURN
        is_break = box.box_header == Token.KEYWORD_BREAK
        is_continue = box.box_header == Token.KEYWORD_CONTINUE
        is_set = box.box_header == Token.KEYWORD_SET
        is_function = (
            box.box_header.startswith(Token.FUNCTION_START)
            and len(box.input_control_flow_ports) == 0
            and len(box.output_control_flow_ports) == 1
        )
        is_function_call = (
            box.box_header.startswith(Token.FUNCTION_START)
            and len(box.input_control_flow_ports) <= 1
            and len(box.output_control_flow_ports) <= 1
        )

        if is_math_operation:
            return OperatorNode(box, self)
        elif is_return:
            return ReturnNode(box, self)
        elif is_break:
            return BreakNode(box, self)
        elif is_continue:
            return ContinueNode(box, self)
        elif is_set:
            return SetNode(box, self)
        elif is_function:
            return FunctionDeclarationNode(box, self)
        elif is_function_call:
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

        while True:
            if len(start.output_control_flow_ports) == 0:
                # End of control flow
                result.append(self._create_node(start))
                return result

            is_math_operation = start.box_header == ""
            is_function = (
                start.box_header.startswith(Token.FUNCTION_START)
                and len(start.input_control_flow_ports) == 0
                and len(start.output_control_flow_ports) == 1
            )
            is_function_call = (
                start.box_header.startswith(Token.FUNCTION_START)
                and len(start.input_control_flow_ports) <= 1
                and len(start.output_control_flow_ports) <= 1
            )
            is_branch = start.box_header == Token.KEYWORD_BRANCH
            is_for_loop = start.box_header == Token.KEYWORD_FOR_LOOP
            is_for_each = start.box_header == Token.KEYWORD_FOR_EACH
            is_while_loop = start.box_header == Token.KEYWORD_WHILE_LOOP
            is_return = start.box_header == Token.KEYWORD_RETURN
            is_break = start.box_header == Token.KEYWORD_BREAK
            is_continue = start.box_header == Token.KEYWORD_CONTINUE
            is_set = start.box_header == Token.KEYWORD_SET

            if is_function:
                result.append(self._create_node(start))

                if len(start.output_control_flow_ports) > 0:
                    start_port = start.output_control_flow_ports[0]
                    end_port = self._find_destination_connection(start_port)
                    end_box = self.port_box_map[end_port]
                    start = end_box
                    continue
                else:
                    break

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
            elif is_break:
                assert len(start.output_control_flow_ports) == 0
                # This is a break statement
                # Break here since there won't be any other statements
                # in this control flow
                result.append(BreakNode(start, self))
                break
            elif is_continue:
                assert len(start.output_control_flow_ports) == 0
                # This is a continue statement
                # Break here since there won't be any other statements
                # in this control flow
                result.append(ContinueNode(start, self))
                break
            elif is_branch:
                assert len(start.output_control_flow_ports) >= 1
                assert len(start.output_control_flow_ports) <= 2
                # Two output control flow ports here
                # The `True` case, and the `False` case
                true_output_port = start.output_control_flow_ports[0]
                true_case_start_port = self._find_destination_connection(
                    true_output_port
                )
                true_case_start_box = self.port_box_map[true_case_start_port]
                true_case_control_flow = self._find_order_of_operations(
                    true_case_start_box, False
                )

                false_case_control_flow = []
                if len(start.output_control_flow_ports) > 1:
                    false_output_port = start.output_control_flow_ports[1]
                    false_case_start_port = self._find_destination_connection(
                        false_output_port
                    )
                    false_case_start_box = self.port_box_map[false_case_start_port]                        
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
                assert len(start.output_control_flow_ports) >= 1
                assert len(start.output_control_flow_ports) <= 2
                # Two output control flow ports here
                # The `Loop body` case, and the `Completed` case
                loop_body_output_port = start.output_control_flow_ports[0]
                loop_body_case_start_port = self._find_destination_connection(
                    loop_body_output_port
                )
                loop_body_case_start_box = self.port_box_map[
                    loop_body_case_start_port
                ]
                loop_body_case_control_flow = self._find_order_of_operations(
                    loop_body_case_start_box, False
                )
                result.append(ForLoopNode(start, loop_body_case_control_flow, self))

                if len(start.output_control_flow_ports) > 1:
                    # Completed case provided
                    completed_output_port = start.output_control_flow_ports[1]
                    completed_case_start_port = self._find_destination_connection(
                        completed_output_port
                    )
                    completed_case_start_box = self.port_box_map[
                        completed_case_start_port
                    ]
                    completed_case_control_flow = self._find_order_of_operations(
                        completed_case_start_box, False
                    )
                    result.extend(completed_case_control_flow)

                break
            elif is_while_loop:
                assert len(start.output_control_flow_ports) >= 1
                assert len(start.output_control_flow_ports) <= 2
                # Two output control flow ports here
                # The `Loop body` case, and the `Completed` case
                loop_body_output_port = start.output_control_flow_ports[0]
                loop_body_case_start_port = self._find_destination_connection(
                    loop_body_output_port
                )
                loop_body_case_start_box = self.port_box_map[
                    loop_body_case_start_port
                ]
                loop_body_case_control_flow = self._find_order_of_operations(
                    loop_body_case_start_box, False
                )
                result.append(
                    WhileLoopNode(start, loop_body_case_control_flow, self)
                )

                if len(start.output_control_flow_ports) > 1:
                    # Completed case provided
                    completed_output_port = start.output_control_flow_ports[1]
                    completed_case_start_port = self._find_destination_connection(
                        completed_output_port
                    )
                    completed_case_start_box = self.port_box_map[
                        completed_case_start_port
                    ]
                    completed_case_control_flow = self._find_order_of_operations(
                        completed_case_start_box, False
                    )
                    result.extend(completed_case_control_flow)

                break

            elif is_for_each:
                assert len(start.input_control_flow_ports) == 1
                assert len(start.output_control_flow_ports) >= 1
                assert len(start.output_control_flow_ports) <= 2
                # Two output control flow ports here
                # The `Loop body` case, and the `Completed` case
                loop_body_output_port = start.output_control_flow_ports[0]
                loop_body_case_start_port = self._find_destination_connection(
                    loop_body_output_port
                )
                loop_body_case_start_box = self.port_box_map[
                    loop_body_case_start_port
                ]
                loop_body_case_control_flow = self._find_order_of_operations(
                    loop_body_case_start_box, False
                )
                result.append(ForEachNode(start, loop_body_case_control_flow, self))

                if len(start.output_control_flow_ports) > 1:
                    # Completed case provided
                    completed_output_port = start.output_control_flow_ports[1]
                    completed_case_start_port = self._find_destination_connection(
                        completed_output_port
                    )
                    completed_case_start_box = self.port_box_map[
                        completed_case_start_port
                    ]
                    completed_case_control_flow = self._find_order_of_operations(
                        completed_case_start_box, False
                    )
                    result.extend(completed_case_control_flow)

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
            else:
                result.append(self._create_node(start))

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
