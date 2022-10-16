# Statements
args = (1, 2)
kwargs = {"x": 1, "y": 2}
x = y = 1
x, y = args
x += 2
assert 1 == 1, "reason"
del kwargs["x"]
pass


import os
import os.path
from os.path import join
from os.path import join as j

# Function definitions
lambda x: x + 1


def decorator(f):
    def decorated(*args, **kwargs):
        return f(*args, **kwargs)

    return decorated


@decorator
@decorator
def ite(cond: "annotation", true=True, false=False):
    if cond:
        return true
    return false


def nums():
    x = 0
    while True:
        yield x
        x += 1


def f(x):
    global y
    y = x

    def g(y):
        nonlocal x
        x = y

    return g


# Class statements
class A(object):
    def __init__(self, x):
        self.x = x


from abc import ABCMeta


@decorator
class B(A, metaclass=ABCMeta):
    pass
