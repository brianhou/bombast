import argparse
import ast
import astunparse
import builtins
import sys

from bombast.transform import *

class Preprocess(ast.NodeVisitor):
    ignores = set(dir(builtins))

    def __init__(self):
        ast.NodeTransformer.__init__(self)
        self.mapping = {}
        self.imports = set()

    def rename(self, input):
        if input in self.ignores:
            return
        elif input in self.imports:
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
        self.imports.add(node.names[0].name)

class Bombast(ast.NodeTransformer):
    def __init__(self, preprocess):
        super().__init__()
        self.mapping = preprocess.mapping
        self.imports = preprocess.imports

    def rename(self, input):
        return self.mapping.get(input, input)

    def visit_Expr(self, node):
        if isinstance(node.value, Str): # docstring
            return Expr(Str(s=random.randident(20, 30), **DEFAULT_CONSTANT_KWARGS))
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
        defaults, kw_defaults = node.defaults, node.kw_defaults
        if VERSION[:2] < (3, 4):
            vararg = self.rename(node.vararg)
            kwarg = self.rename(node.kwarg)
            as_kwargs = dict(args=args, vararg=vararg, varargannotation=node.varargannotation,
                             kwonlyargs=kwonlyargs, kwarg=kwarg, kwargannotation=node.kwargannotation,
                             defaults=defaults, kw_defaults=kw_defaults)
        else:
            posonlyargs = [self.visit(posonlyarg) for posonlyarg in node.posonlyargs] if VERSION[:2] >= (3, 8) else []
            vararg = kwarg = None
            if node.vararg is not None:
                vararg = arg(arg=self.rename(node.vararg.arg), annotation=node.vararg.annotation)
            if node.kwarg is not None:
                kwarg = arg(arg=self.rename(node.kwarg.arg), annotation=node.kwarg.annotation)
            as_kwargs = dict(posonlyargs=posonlyargs, args=args, vararg=vararg, kwonlyargs=kwonlyargs, kw_defaults=kw_defaults, kwarg=kwarg, defaults=defaults)
        for key in list(as_kwargs.keys()):
            if key not in arguments._fields:
                del as_kwargs[key]
        return arguments(**as_kwargs)

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
        if VERSION[:2] < (3, 5):
            return ClassDef(name, bases,
                            node.keywords, node.starargs, node.kwargs,
                            body, decorator_list)
        else:
            return ClassDef(name, bases,
                            node.keywords, body, decorator_list)

    def visit_JoinedStr(self, node):
        new_node = None
        for value in node.values:
            if type(value) == Constant:
                value = self.visit(value)
            elif type(value) == FormattedValue:
                value.value = self.visit(value.value)
                value = JoinedStr(values=[value])
            else:
                raise RuntimeError('Invalid node in JoinedStr')

            if new_node is None:
                new_node = value
            else:
                new_node = BinOp(
                    left=new_node,
                    right=value,
                    op=Add()
                )
        return new_node

def configure(path):
    options = load_config(path)
    for option, value in options.items():
        if option == 'ignore_names':
            user_ignores = set(value)
            Preprocess.ignores |= user_ignores
        else:
            print('Warning: option "{}" is unused.'.format(option),
                  file=sys.stderr)

def main():
    parser = argparse.ArgumentParser(description='Obfuscate Python source code.')
    parser.add_argument('infile', type=argparse.FileType('rb'),
                        default=sys.stdin,
                        help='input')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default='obfuscated.py',
                        help='output [default: obfuscated.py]')
    parser.add_argument('--seed', type=int, default=0,
                        help='random seed [default: 0]')
    parser.add_argument('--iters', type=int, default=1,
                        help='number of iterations [default: 1]')
    parser.add_argument('--config', type=str,
                        help='configuration file [default: bombast.config]')
    parser.add_argument('--show-translations', action='store_true',
                        help='print translations to stdout')
    args = parser.parse_args()
    configure(args.config)

    random.seed(args.seed)
    root = ast.parse(args.infile.read())

    # Choose renamings
    preprocess = Preprocess()
    preprocess.visit(root)

    bombast = Bombast(preprocess)
    for _ in range(args.iters):
        root = bombast.visit(root)

    # Postprocessing
    root.body.sort(key=lambda x: not isinstance(x, ast.Import)) # move imports
    ast.fix_missing_locations(root) # fix AST

    print(astunparse.unparse(root), file=args.outfile)
    if args.show_translations:
        for original, obfuscated in preprocess.mapping.items():
            print(original, '=', obfuscated)

if __name__ == '__main__':
    main()
