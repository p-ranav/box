
class BoxIterator:
    def __init__(self, lines, current_x, current_y):
        self.lines = lines
        self.current_x = current_x
        self.current_y = current_y

    def current(self):
        if self.current_x < len(self.lines):
            if self.current_y < len(self.lines[self.current_x]):
                return self.lines[self.current_x][self.current_y]
        return None

    def right(self):
        self.current_y += 1

    def left(self):
        self.current_y -= 1

    def top(self):
        self.current_x -= 1

    def bottom(self):
        self.current_x += 1

    def pos(self):
        return (self.current_x, self.current_y)
