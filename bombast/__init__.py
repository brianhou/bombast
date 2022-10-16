"""bombast obfuscates Python 3 source code by manipulating the AST.

bombast replaces names with a random new identifier, then repeatedly applies
various transformations to the AST.
"""


import argparse
import ast
import builtins
import functools
import random
import sys

from bombast import transform, utils


class Preprocess(ast.NodeVisitor):
    """A NodeVisitor that assigns all identifiers in the AST new names.

    Names in ``Preprocess.ignores`` are untouched. By default, this contains all
    builtins; define ignore_names in bombast.config to customize further.
    """

    ignores = set(dir(builtins))

    def __init__(self):
        super().__init__()
        self.mapping = {}
        self.imports = set()

    def rename(self, name):
        if name in self.imports:
            return
        if name in self.ignores or name in self.mapping:
            return
        new_name = utils.randident(4, 10)
        while new_name in self.mapping.values():
            new_name = utils.randident(4, 10)
        self.mapping[name] = new_name

    def visit_Name(self, node):
        self.rename(node.id)

    def visit_FunctionDef(self, node):
        if not node.name.startswith("__"):
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
    """A NodeTransformer that applies ``Transformations`` to the AST."""

    def __init__(self, preprocess):
        super().__init__()
        self.mapping = preprocess.mapping
        self.imports = preprocess.imports

    def rename(self, name):
        return self.mapping.get(name, name)

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(
            node.value.value, str
        ):  # docstring
            return ast.Expr(ast.Constant(value=utils.randident(20, 30)))
        return ast.Expr(self.visit(node.value))

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            return ast.Constant(value=node.value)
        elif isinstance(node.value, (int, float)):
            return transform.NumBombast(node).transform()
        elif isinstance(node.value, str):
            return transform.StrBombast(node).transform()
        return ast.Constant(value=node.value)

    def visit_Name(self, node):
        return ast.Name(id=self.rename(node.id), ctx=node.ctx)

    def visit_Attribute(self, node):
        if isinstance(node.value, ast.Name) and node.value.id in self.imports:
            attr = node.attr
        else:
            attr = self.rename(node.attr)
        return ast.Attribute(value=self.visit(node.value), attr=attr, ctx=node.ctx)

    def visit_ExceptHandler(self, node):
        return ast.ExceptHandler(
            type=node.type if node.type is None else self.visit(node.type),
            name=self.rename(node.name),
            body=[self.visit(b) for b in node.body],
        )

    def visit_arg(self, node):
        return ast.arg(arg=self.rename(node.arg), annotation=node.annotation)

    def visit_keyword(self, node):
        return ast.keyword(arg=self.rename(node.arg), value=self.visit(node.value))

    def visit_arguments(self, node):
        args = [self.visit(arg) for arg in node.args]
        kwonlyargs = [self.visit(arg) for arg in node.kwonlyargs]
        defaults, kw_defaults = node.defaults, node.kw_defaults
        posonlyargs = [self.visit(posonlyarg) for posonlyarg in node.posonlyargs]
        vararg = kwarg = None
        if node.vararg is not None:
            vararg = ast.arg(
                arg=self.rename(node.vararg.arg), annotation=node.vararg.annotation
            )
        if node.kwarg is not None:
            kwarg = ast.arg(
                arg=self.rename(node.kwarg.arg), annotation=node.kwarg.annotation
            )
        as_kwargs = dict(
            posonlyargs=posonlyargs,
            args=args,
            vararg=vararg,
            kwonlyargs=kwonlyargs,
            kw_defaults=kw_defaults,
            kwarg=kwarg,
            defaults=defaults,
        )
        return ast.arguments(**as_kwargs)

    def visit_FunctionDef(self, node):
        name = self.rename(node.name)
        args = self.visit(node.args)
        body = [self.visit(b) for b in node.body]
        decorator_list = [self.visit(d) for d in node.decorator_list]
        return ast.FunctionDef(name, args, body, decorator_list, node.returns)

    def visit_Global(self, node):
        return ast.Global([self.rename(n) for n in node.names])

    def visit_Nonlocal(self, node):
        return ast.Nonlocal([self.rename(n) for n in node.names])

    def visit_ClassDef(self, node):
        name = self.rename(node.name)
        bases = [self.visit(b) for b in node.bases]
        body = [self.visit(b) for b in node.body]
        decorator_list = [self.visit(d) for d in node.decorator_list]
        return ast.ClassDef(name, bases, node.keywords, body, decorator_list)

    def visit_FormattedValue(self, node):
        value = self.visit(node.value)
        return ast.FormattedValue(
            value=value,
            conversion=node.conversion,
            format_spec=node.format_spec,
        )

    def visit_JoinedStr(self, node):
        return functools.reduce(
            lambda x, y: ast.BinOp(left=x, right=y, op=ast.Add()),
            (self.visit(value) for value in node.values),
        )


def configure(path):
    options = utils.load_config(path)
    for option, value in options.items():
        if option == "ignore_names":
            user_ignores = set(value)
            Preprocess.ignores |= user_ignores
        else:
            print(f"Warning: {option=} is unused.", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Obfuscate Python source code.")
    parser.add_argument(
        "infile", type=argparse.FileType("rb"), default=sys.stdin, help="input"
    )
    parser.add_argument(
        "outfile",
        nargs="?",
        type=argparse.FileType("w"),
        default="obfuscated.py",
        help="output [default: obfuscated.py]",
    )
    parser.add_argument("--seed", type=int, default=0, help="random seed [default: 0]")
    parser.add_argument(
        "--iters", type=int, default=1, help="number of iterations [default: 1]"
    )
    parser.add_argument(
        "--config", type=str, help="configuration file [default: bombast.config]"
    )
    parser.add_argument(
        "--show-translations", action="store_true", help="print translations to stdout"
    )
    args = parser.parse_args()
    configure(args.config)

    random.seed(args.seed)
    root = ast.parse(args.infile.read())
    args.infile.close()

    # Choose renamings
    preprocess = Preprocess()
    preprocess.visit(root)

    bombast = Bombast(preprocess)
    for _ in range(args.iters):
        root = bombast.visit(root)

    # Postprocessing
    root.body.sort(key=lambda x: not isinstance(x, ast.Import))  # move imports
    ast.fix_missing_locations(root)  # fix AST

    print(ast.unparse(root), file=args.outfile)
    args.outfile.close()
    if args.show_translations:
        for original, obfuscated in preprocess.mapping.items():
            print(original, "=", obfuscated)


if __name__ == "__main__":
    main()
