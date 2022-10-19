import ast
import random
from typing import Callable, TypeVar, Generic


T = TypeVar("T", bound=ast.AST)


class Transform(Generic[T]):
    """A possible AST transformation."""

    def __call__(self, node: T) -> ast.AST:
        return node


class RandomTransform(Transform[T]):
    """A set of possible AST transformations."""

    def __init__(self, *funcs: Callable[[T], ast.AST]):
        self.funcs = list(funcs)

    def register(self, func: Callable[[T], ast.AST]):
        self.funcs.append(func)
        return func

    def __call__(self, node: T) -> ast.AST:
        """Return a random transformation of the input node."""
        if not self.funcs:
            return super().__call__(node)
        return random.choice(self.funcs)(node)


################
# StrTransform #
################


class _StrTransform(Transform[ast.Constant]):
    def __init__(self):
        self.transform_empty: RandomTransform[ast.Constant] = RandomTransform()
        self.transform_char: RandomTransform[ast.Constant] = RandomTransform()
        self.transform_str: RandomTransform[ast.Constant] = RandomTransform()

    def __call__(self, node: ast.Constant) -> ast.AST:
        s = node.value
        if len(s) == 0:
            return self.transform_empty(node)
        elif len(s) == 1:
            return self.transform_char(node)
        else:
            return self.transform_str(node)


StrTransform = _StrTransform()


@StrTransform.transform_empty.register
def _empty_constructor(node: ast.Constant):
    """Transform an empty string into a str constructor call."""
    return ast.Call(
        func=ast.Name(id="str", ctx=ast.Load()),
        args=[],
        keywords=[],
        starargs=None,
        kwargs=None,
    )


@StrTransform.transform_empty.register
def _empty_identity(node: ast.Constant):
    return node


@StrTransform.transform_char.register
def _char_chr(node: ast.Constant):
    """Transform a character s into a chr call."""
    return ast.Call(
        func=ast.Name(id="chr", ctx=ast.Load()),
        args=[ast.Constant(value=ord(node.value))],
        keywords=[],
        starargs=None,
        kwargs=None,
    )


@StrTransform.transform_char.register
def _char_identity(node: ast.Constant):
    return node


@StrTransform.transform_str.register
def _str_split(node: ast.Constant):
    """Transform a string s into s[:i] + s[i:]."""
    s = node.value
    i = random.randrange(len(s))
    return ast.BinOp(
        left=ast.Constant(value=s[:i]),
        right=ast.Constant(value=s[i:]),
        op=ast.Add(),
    )


################
# NumTransform #
################


class _NumTransform(Transform[ast.Constant]):
    def __init__(self):
        self.transform_zero: RandomTransform[ast.Constant] = RandomTransform()
        self.transform_int: RandomTransform[ast.Constant] = RandomTransform()
        self.transform_float: RandomTransform[ast.Constant] = RandomTransform()

    def __call__(self, node: ast.Constant) -> ast.AST:
        n = node.value
        if n == 0:
            return self.transform_zero(node)
        elif isinstance(n, int):
            return self.transform_int(node)
        else:
            return self.transform_float(node)


NumTransform = _NumTransform()


@NumTransform.transform_zero.register
def _zero_mult(node: ast.Constant):
    """Transform an integer 0 into int(r * 0)."""
    return ast.Call(
        func=ast.Name(id="int", ctx=ast.Load()),
        args=[
            ast.BinOp(
                left=ast.Constant(value=random.random()),
                right=ast.Constant(value=0),
                op=ast.Mult(),
            )
        ],
        keywords=[],
        starargs=None,
        kwargs=None,
    )


@NumTransform.transform_zero.register
def _zero_identity(node: ast.Constant):
    return node


@NumTransform.transform_int.register
def _int_split(node: ast.Constant, range: int = 100):
    """Transform an integer n into (n - r) + r"""
    r = random.randint(-range, range)
    return ast.BinOp(
        left=ast.Constant(value=node.value - r),
        right=ast.Constant(value=r),
        op=ast.Add(),
    )


@NumTransform.transform_float.register
def _float_split(node: ast.Constant):
    """Transform a float n into (n - r) + r"""
    r = random.random()
    return ast.BinOp(
        left=ast.Constant(value=node.value - r),
        right=ast.Constant(value=r),
        op=ast.Add(),
    )
