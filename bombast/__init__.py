import argparse
import ast
import astunparse
import sys

from transform import *

class Bombast(ast.NodeTransformer):
    def __init__(self):
        self.global_rename = {}
        self.local_rename = {}

    def visit_Num(self, node):
        return NumBombast(node).transform()

    def visit_Str(self, node):
        return StrBombast(node).transform()

    def visit_Import(self, node):
        return ImportBombast(node, self).transform()
Bombast = Bombast()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Obfuscate Python source code.')
    parser.add_argument('pyfile', help='input')
    parser.add_argument('--iters', help='number of iterations', type=int, default=3)
    args = parser.parse_args()
    if args.pyfile == '-':
        root = ast.parse(sys.stdin.read())
    else:
        root = ast.parse(open(args.pyfile, 'rb').read())

    for _ in range(args.iters):
        root = Bombast.visit(root)
    ast.fix_missing_locations(root)
    print(astunparse.unparse(root))
