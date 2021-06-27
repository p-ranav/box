from box.parser import Parser
import os
import sys

def main(filename):
    path = os.path.join(os.getcwd(), filename)
    parser = Parser(path)

    for box in parser.boxes:
        print(box.box_header, box.top_left, box.top_right, box.bottom_right, box.bottom_left)

if __name__ == "__main__":
    main(sys.argv[1])
