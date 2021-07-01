import argparse
from box.parser import Parser
from box.generator import Generator
import logging
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

    if args.v:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.WARNING)    

    filename = args.path

    eval_args = args.e
    verbosity = args.v
    path = os.path.join(os.getcwd(), filename)

    logging.debug("Reading file " + filename)
    
    parser = Parser(path)

    logging.debug("Parsed file at " + filename)
    generator = Generator(parser)
    
    logging.debug("Generating Python... " + filename)

    code = generator.to_python(args.e)

    if args.o:
        with open(os.path.abspath(args.o), 'w') as output:
            logging.debug("Writing generated Python to " + args.o)
            output.write(code)

    exec(code)

if __name__ == "__main__":
    main()
