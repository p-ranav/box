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
            if self.current_y >= 1 and (self.current_y - 1) < len(
                self.lines[self.current_x]
            ):
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
