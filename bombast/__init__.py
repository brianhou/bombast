import argparse
import ast
import astunparse
import sys

from bombast.transform import *

class Preprocess(ast.NodeVisitor):
    hardcoded = ['f_locals', 'add']
    ignores = dir(__builtins__) + hardcoded

    def __init__(self):
        ast.NodeTransformer.__init__(self)
        self.mapping = {}
        self.imports = []

    def rename(self, input):
        if input in self.ignores or input in self.imports:
            return
        new_name = random.randident(4, 10)
        while new_name in self.mapping.values():
            new_name = random.randident(4, 10)
        self.mapping[input] = new_name

    def visit_Name(self, node):
        self.rename(node.id)

    def visit_FunctionDef(self, node):
        if not node.name.startswith('__'):
            self.rename(node.name)
        self.visit(node.args)
        for line in node.body:
            self.visit(line)

    def visit_ClassDef(self, node):
        self.rename(node.name)
        for base in node.bases:
            self.visit(base)
        for line in node.body:
            self.visit(line)

    def visit_Import(self, node):
        # only supports imports of the form 'import <module>'
        self.imports.append(node.names[0].name)

class Bombast(ast.NodeTransformer):
    def __init__(self, preprocess):
        super().__init__()
        self.mapping = preprocess.mapping
        self.imports = preprocess.imports

    def rename(self, input):
        return self.mapping.get(input, input)

    def visit_Expr(self, node):
        if isinstance(node.value, Str): # docstring
            return Expr(Str(s=random.randident(20, 30)))
        return Expr(self.visit(node.value))

    def visit_Num(self, node):
        return NumBombast(node).transform()

    def visit_Str(self, node):
        return StrBombast(node).transform()

    def visit_Name(self, node):
        return Name(id=self.rename(node.id), ctx=node.ctx)

    def visit_Attribute(self, node):
        if isinstance(node.value, Name) and node.value.id in self.imports:
            attr = node.attr
        else:
            attr = self.rename(node.attr)
        return Attribute(value=self.visit(node.value), attr=attr, ctx=node.ctx)

    def visit_ExceptHandler(self, node):
        return ExceptHandler(type=node.type if node.type is None else self.visit(node.type),
                             name=self.rename(node.name),
                             body=[self.visit(b) for b in node.body])

    def visit_arg(self, node):
        return arg(arg=self.rename(node.arg), annotation=node.annotation)

    def visit_keyword(self, node):
        return keyword(arg=self.rename(node.arg), value=self.visit(node.value))

    def visit_arguments(self, node):
        args = [self.visit(arg) for arg in node.args]
        kwonlyargs = [self.visit(arg) for arg in node.kwonlyargs]
        vararg = self.rename(node.vararg)
        kwarg = self.rename(node.kwarg)
        defaults, kw_defaults = node.defaults, node.kw_defaults
        if VERSION.minor < 4:
            return arguments(args, vararg, node.varargannotation,
                             kwonlyargs, kwarg, node.kwargannotation,
                             defaults, kw_defaults)
        else:
            return arguments(args, vararg, kwonlyargs, kwarg, defaults, kw_defaults)

    def visit_FunctionDef(self, node):
        name = self.rename(node.name)
        args = self.visit(node.args)
        body = [self.visit(b) for b in node.body]
        decorator_list = [self.visit(d) for d in node.decorator_list]
        return FunctionDef(name, args, body, decorator_list, node.returns)

    def visit_Global(self, node):
        return Global([self.rename(n) for n in node.names])

    def visit_Nonlocal(self, node):
        return Nonlocal([self.rename(n) for n in node.names])

    def visit_ClassDef(self, node):
        name = self.rename(node.name)
        bases = [self.visit(b) for b in node.bases]
        body = [self.visit(b) for b in node.body]
        decorator_list = [self.visit(d) for d in node.decorator_list]
        return ClassDef(name, bases,
                        node.keywords, node.starargs, node.kwargs,
                        body, decorator_list)

def main():
    parser = argparse.ArgumentParser(description='Obfuscate Python source code.')
    parser.add_argument('pyfile', help='input')
    parser.add_argument('--iters', help='number of iterations', type=int, default=1)
    args = parser.parse_args()
    if args.pyfile == '-':
        root = ast.parse(sys.stdin.read())
    else:
        root = ast.parse(open(args.pyfile, 'rb').read())

    # Choose renamings
    preprocess = Preprocess()
    preprocess.visit(root)

    bombast = Bombast(preprocess)
    for _ in range(args.iters):
        root = bombast.visit(root)
    ast.fix_missing_locations(root)
    print(astunparse.unparse(root))

if __name__ == '__main__':
    main()
