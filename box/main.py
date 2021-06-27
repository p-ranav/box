from box.parser import Parser
import os
import sys

def main(filename):
    path = os.path.join(os.getcwd(), filename)
    parser = Parser(path)

if __name__ == "__main__":
    main(sys.argv[1])
