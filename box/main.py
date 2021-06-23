from box_parser import detect_boxes
from box import build_parse_tree

# find box that is left-most and top-most
# this is the chosen parent
# find all boxes that are INSIDE this parent
# 

def main(filename = "test.box"):
    boxes = detect_boxes(filename)
    root = build_parse_tree(boxes)
    root.print()
        
if __name__ == "__main__":
    main()