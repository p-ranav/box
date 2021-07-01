from box.parser import Parser
from box.generator import Generator
import os

class Importer:
    def __init__(self, path):
        # Path to directory containing function graphs to import
        self.path = os.path.abspath(path)

        # { "FunctionName": <Generator>, ... }
        self.function_declarations = {}        

        # List of (Parser, Generator) objects,
        # one for each function graph .box file
        self.parser_generators = self._parse_box_files()

        print(self.function_declarations)
    
    def _parse_box_files(self):
        # Result is a list of tuples [(parser, generator), ...]
        result = [] 
        for file in os.listdir(self.path):
            if file.endswith(".box"):
                path = os.path.join(self.path, file)
                parser = Parser(path)
                generator = Generator(parser)
                code = generator.to_python([])
                result.append((parser, generator))
                self.function_declarations[generator.function_name] = generator
        return result

    
