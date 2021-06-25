from box_parser import detect_boxes, build_parse_tree
from transpiler import Transpiler
import sys

def main(filename):
    lines, boxes = detect_boxes(filename)
    root = build_parse_tree(lines, boxes)
    transpiler = Transpiler(root)
    
    if transpiler.is_function(root):
        print(transpiler.to_python())

if __name__ == "__main__":
    main(sys.argv[1])
