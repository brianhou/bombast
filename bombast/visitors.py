import ast
import builtins
import functools
import random
import string
from typing import Optional

from bombast import transforms


FIRST_CHAR = string.ascii_uppercase + string.ascii_lowercase
OTHER_CHAR = (
    string.ascii_uppercase + string.ascii_lowercase + string.digits * 5 + "_" * 20
)


def randident(a: int, b: Optional[int] = None) -> str:
    """Return a random Python identifier."""
    length = None
    try:
        length = random.randrange(a, b)
    except:
        pass
    if length is None or b is None:
        length = a
    return random.choice(FIRST_CHAR) + "".join(
        random.choice(OTHER_CHAR) for _ in range(length - 1)
    )


class Preprocess(ast.NodeVisitor):
    """A NodeVisitor that assigns all identifiers in the AST new names.

    Names in ``Preprocess.ignores`` are untouched. By default, this contains all
    builtins; define "ignore_names" in bombast.config to customize further.
    """

    def __init__(self, ignore_names: Optional[list[str]] = None, **kwargs):
        super().__init__()
        if ignore_names is None:
            ignore_names = []
        self.ignores: set[str] = set(dir(builtins)) | set(ignore_names)
        self.mapping: dict[str, str] = {}
        self.imports: set[str] = set()

    def rename(self, name: str):
        """Assign a new identifier for NAME."""
        if name in self.imports:
            return
        if name in self.ignores or name in self.mapping:
            return
        new_name = randident(4, 10)
        while new_name in self.mapping.values():
            new_name = randident(4, 10)
        self.mapping[name] = new_name

    def visit_Name(self, node: ast.Name):
        """A variable name."""
        self.rename(node.id)

    def visit_Import(self, node: ast.Import):
        """An import statement."""
        # only supports imports of the form 'import <module>'
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """A function definition."""
        if not node.name.startswith("__"):
            self.rename(node.name)
        self.visit(node.args)
        for line in node.body:
            self.visit(line)

    def visit_ClassDef(self, node: ast.ClassDef):
        """A class definition."""
        self.rename(node.name)
        for base in node.bases:
            self.visit(base)
        for line in node.body:
            self.visit(line)


class Bombast(ast.NodeTransformer):
    """A NodeTransformer that applies ``Transformations`` to the AST."""

    def __init__(self, preprocess, **kwargs):
        super().__init__()
        self.mapping = preprocess.mapping
        self.imports = preprocess.imports

    def rename(self, name):
        return self.mapping.get(name, name)

    def optional(self, func, node):
        return None if node is None else func(node)

    def visit_Constant(self, node: ast.Constant):
        """A constant value."""
        if isinstance(node.value, bool):
            return ast.Constant(value=node.value)
        elif isinstance(node.value, (int, float)):
            return transforms.NumTransform(node)
        elif isinstance(node.value, str):
            return transforms.StrTransform(node)
        return ast.Constant(value=node.value)

    def visit_FormattedValue(self, node: ast.FormattedValue):
        """A single formatting field in an f-string."""
        return ast.FormattedValue(
            value=self.visit(node.value),
            conversion=node.conversion,
            format_spec=node.format_spec,
        )

    def visit_JoinedStr(self, node: ast.JoinedStr):
        """An f-string, comprising a series of FormattedValue and Constant nodes."""
        return functools.reduce(
            lambda x, y: ast.BinOp(left=x, right=y, op=ast.Add()),
            (self.visit(value) for value in node.values),
        )

    def visit_Name(self, node: ast.Name):
        """A variable name."""
        return ast.Name(id=self.rename(node.id), ctx=node.ctx)

    def visit_Expr(self, node: ast.Expr):
        """An expression that appears as a statement by itself."""
        # Transform docstrings into a random string.
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return ast.Expr(ast.Constant(value=randident(20, 30)))
        return ast.Expr(self.visit(node.value))

    def visit_Attribute(self, node: ast.Attribute):
        """Attribute access."""
        if isinstance(node.value, ast.Name) and node.value.id in self.imports:
            attr = node.attr
        else:
            attr = self.rename(node.attr)
        return ast.Attribute(value=self.visit(node.value), attr=attr, ctx=node.ctx)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        """A single except clause."""
        type = self.optional(self.visit, node.type)
        name = self.optional(self.rename, node.name)
        body = [self.visit(b) for b in node.body]
        return ast.ExceptHandler(type, name, body)

    def visit_arguments(self, node: ast.arguments):
        """The arguments for a function."""
        posonlyargs = [self.visit(posonlyarg) for posonlyarg in node.posonlyargs]
        args = [self.visit(arg) for arg in node.args]
        vararg = self.optional(self.visit, node.vararg)
        kwonlyargs = [self.visit(arg) for arg in node.kwonlyargs]
        kw_defaults = node.kw_defaults
        kwarg = self.optional(self.visit, node.kwarg)
        defaults = node.defaults
        return ast.arguments(
            posonlyargs, args, vararg, kwonlyargs, kw_defaults, kwarg, defaults
        )

    def visit_arg(self, node: ast.arg):
        """A single argument in a list."""
        return ast.arg(arg=self.rename(node.arg), annotation=node.annotation)

    def visit_keyword(self, node: ast.keyword):
        """A keyword argument to a function call or class definition."""
        return ast.keyword(arg=self.rename(node.arg), value=self.visit(node.value))

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """A function definition."""
        name = self.rename(node.name)
        args = self.visit(node.args)
        body = [self.visit(b) for b in node.body]
        decorator_list = [self.visit(d) for d in node.decorator_list]
        returns = node.returns
        return ast.FunctionDef(name, args, body, decorator_list, returns)

    def visit_Global(self, node: ast.Global):
        """A global statement."""
        return ast.Global([self.rename(n) for n in node.names])

    def visit_Nonlocal(self, node: ast.Nonlocal):
        """A nonlocal statement."""
        return ast.Nonlocal([self.rename(n) for n in node.names])

    def visit_ClassDef(self, node: ast.ClassDef):
        """A class definition."""
        name = self.rename(node.name)
        bases = [self.visit(b) for b in node.bases]
        body = [self.visit(b) for b in node.body]
        decorator_list = [self.visit(d) for d in node.decorator_list]
        return ast.ClassDef(name, bases, node.keywords, body, decorator_list)
