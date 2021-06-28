import argparse
from box.parser import Parser
import os

def main(args):

    filename = args.path
    eval_args = args.e
    verbosity = args.v
    
    path = os.path.join(os.getcwd(), filename)
    parser = Parser(path)
    code = parser.to_python()

    function_name = parser.function_name
    
    code += "\n"
    if parser.has_return:
        code += "print("
    code += function_name + "("

    if eval_args:
        for i, arg in enumerate(eval_args):
            code += arg
            if i < len(eval_args) - 1:
                code += ", "
    
    code += ")"
    if parser.has_return:
        code += ")"

    if (args.v):
        print(code)

    exec(code)

if __name__ == "__main__":    
    parser = argparse.ArgumentParser(description='Box interpreter')
    parser.add_argument("path", help="Path to box file")
    parser.add_argument('-v', action="store_true", help='Toggle verbosity')
    parser.add_argument('-e', nargs="+", help='Arguments to pass to box function')
    args = parser.parse_args()
    main(args)

