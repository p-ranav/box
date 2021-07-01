import logging
import uuid


class Box:
    def __init__(
        self,
        box_header,
        box_contents,
        top_left,
        top_right,
        bottom_right,
        bottom_left,
        input_data_flow_ports,
        input_control_flow_ports,
        output_data_flow_ports,
        output_control_flow_ports,
    ):
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
        logging.debug("Constructed box with UUID: " + str(self.uuid))

    def uuid_short(self):
        return str(self.uuid)[:8]
