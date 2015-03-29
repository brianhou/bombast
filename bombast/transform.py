from ast import Num, Str, List, Tuple, Set, Dict # NameConstant
from ast import Name, Load, Store, Del, Starred
from ast import Expr, UnaryOp, UAdd, USub, Not, BinOp
from ast import Add, Sub, Mult, Div, FloorDiv, Mod, Pow
from ast import BoolOp, And, Or, Compare, Eq, NotEq, Lt, LtE, Gt, GtE, Is, IsNot, In, NotIn
from ast import Call, keyword, IfExp, Attribute
from ast import Subscript, Index, Slice
from ast import ListComp, SetComp, DictComp, GeneratorExp, comprehension
from ast import Assign, AugAssign, Raise, Assert, Delete, Pass
from ast import Import, ImportFrom, alias
from ast import If, For, While, Break, Continue, ExceptHandler
from ast import With, withitem
from ast import FunctionDef, Lambda, arguments, arg, Return, Yield, Global, Nonlocal
from ast import ClassDef

from utils import *

class Transformation(object):
    def __init__(self, *fns):
        self.fns = fns

    def transform(self, input):
        if self.fns:
            return random.choice(self.fns)(input)
        return input


class PrimitiveBombast(object):
    def __init__(self, node):
        self.node = node

    def transform(self, input):
        return input


class RenameBombast(PrimitiveBombast):
    def __init__(self, node, bombast):
        super().__init__(node)
        self.bombast = bombast


class StrBombast(PrimitiveBombast):
    def transform(self):
        s = self.node.s
        if len(s) == 0:
            return self.zero.transform(self.node)
        elif len(s) == 1:
            return self.one.transform(self.node)
        else:
            return self.many.transform(self.node)

    def zero_Constructor(node): # '' -> str()
        return Call(func=Name(id='str', ctx=Load()),
                    args=[], keywords=[], starargs=None, kwargs=None)
    def zero_Identity(node): # '' -> ''
        return node
    zero = Transformation(zero_Constructor, zero_Identity)

    def one_Ordinal(node): # 'a' -> chr(97)
        return Call(func=Name(id='chr', ctx=Load()),
                    args=[Num(ord(node.s))], keywords=[], starargs=None, kwargs=None)
    def one_Identity(node): # 'a' -> 'a'
        return node
    one = Transformation(one_Ordinal, one_Identity)

    def many_Split(node): # 'hello' -> 'h' + 'ello' (with randomly chosen cut)
        s = node.s
        i = random.randrange(len(s))
        return BinOp(
            left=Str(s=s[:i]),
            right=Str(s=s[i:]),
            op=Add()
        )
    many = Transformation(many_Split)


class NumBombast(PrimitiveBombast):
    def transform(self):
        n = self.node.n
        if not n:
            return self.zero.transform(self.node)
        elif isinstance(n, int):
            return self.int.transform(self.node)
        else:
            return self.float.transform(self.node)

    def zero_Multiplier(node): # 0 -> int(n * 0)
        return Call(
            func=Name(id='int', ctx=Load()),
            args=[BinOp(left=Num(n=random.random()), right=Num(n=0), op=Mult())],
            keywords=[], starargs=None, kwargs=None
        )
    def zero_Identity(node):
        return node
    zero = Transformation(zero_Multiplier, zero_Identity)

    def int_Split(node, range=100): # n -> (n-s) + (s)
        s = random.randint(-range, range)
        return BinOp(
            left=Num(n=node.n-s),
            right=Num(n=s),
            op=Add()
        )
    int = Transformation(int_Split)

    def float_Split(node): # n -> (n-s) + (s)
        s = random.random()
        return BinOp(
            left=Num(n=node.n-s),
            right=Num(n=s),
            op=Add()
        )
    float = Transformation(float_Split)


class ImportBombast(RenameBombast):
    # import sys -> sys = __import__('sys', globals(), locals(), [], 0)
    one = Transformation(
        lambda n: Assign(
            targets=[Name(id=n.names[0].name, ctx=Store())],
            value=Call(func=Name(id='__import__', ctx=Load()),
                       args=[
                           Str(s=n.names[0].name),
                           Call(func=Name(id='globals', ctx=Load()),
                                args=[], keywords=[], starargs=None, kwargs=None),
                           Call(func=Name(id='locals', ctx=Load()),
                                args=[], keywords=[], starargs=None, kwargs=None),
                           List(elts=[], ctx=Load()),
                           Num(n=0)
                       ],
                       keywords=[], starargs=None, kwargs=None))
        )

    def transform(self):
        num_imports = len(self.node.names)
        if num_imports == 1:
            return self.one.transform(self.node)
        else:
            return self.node
