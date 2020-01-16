
from os import listdir
from os.path import basename, dirname, join
import os, sys

print(os.listdir("."))
print(listdir("."))

print(sys.version)
print(basename("a/b.py"), dirname("a/b.py"), join("a", "b", "c"))

path = 2

# def f(path): return path

sys.path.insert(0, "hi")
