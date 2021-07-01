import argparse
from box.parser import Parser
from box.generator import Generator
from box.importer import Importer
import os


def main():

    parser = argparse.ArgumentParser(description="Box interpreter")
    parser.add_argument("path", help="Path to box file")
    parser.add_argument("-v", action="store_true", help="Toggle verbosity")
    parser.add_argument("-e", nargs="*", help="Arguments to pass to box function")
    parser.add_argument("-I", help="Directory containing function graphs to import")    
    args = parser.parse_args()

    filename = args.path
    eval_args = args.e
    verbosity = args.v
    import_path = args.I

    importer = Importer(import_path)

    path = os.path.join(os.getcwd(), filename)
    parser = Parser(path)
    generator = Generator(parser)

    code = generator.to_python(args.e)

    if args.v:
        print(code)

    exec(code)


if __name__ == "__main__":
    main()
