from box.parser import Parser
import os
import sys

def print_box(box):
    if type(box) == type(Parser.BranchControlFlow([], [])):
        print("BRANCH")
        print("TRUE CASE")
        for i in box.true_case:
            print_box(i)
        print("END OF TRUE CASE")
        print("FALSE CASE")            
        for i in box.false_case:
            print_box(i)
        print("END OF FALSE CASE")
        print("END OF BRANCH")
    elif type(box) == type(Parser.ForLoopControlFlow([])):
        print("FOR LOOP")
        print("START OF LOOP BODY")
        for i in box.loop_body:
            print_box(i)
        print("END OF LOOP BODY")
    else:
        print(type(box), box.box.box_header)

def main(filename):
    path = os.path.join(os.getcwd(), filename)
    parser = Parser(path)

    for node in parser.flow_of_control:
        print_box(node)

    code = parser.to_python()
    print(code)

if __name__ == "__main__":
    main(sys.argv[1])
