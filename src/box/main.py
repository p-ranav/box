import argparse
from box.parser import Parser
from box.generator import Generator
import os


def main():

    parser = argparse.ArgumentParser(description="Box interpreter")
    parser.add_argument("path", help="Path to box file")
    parser.add_argument("-v", action="store_true", help="Toggle verbosity")
    parser.add_argument("-o", help="Path where to store the generated Python code")    
    parser.add_argument("-e", nargs="*", help="Arguments to pass to box function")

    # TODO: Figure out the design for imports (or even to support it)
    # parser.add_argument("-I", help="Directory containing function graphs to import")
    
    args = parser.parse_args()

    filename = args.path
    eval_args = args.e
    verbosity = args.v
    path = os.path.join(os.getcwd(), filename)
    parser = Parser(path)
    generator = Generator(parser)

    code = generator.to_python(args.e)

    if args.v:
        print(code)

    if args.o:
        with open(os.path.abspath(args.o), 'w') as output:
            output.write(code)

    exec(code)

if __name__ == "__main__":
    main()
