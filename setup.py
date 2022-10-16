from setuptools import setup

setup(
    name="bombast",
    version="v0.3.0",
    description="An obfuscator for Python 3 source code that manipulates the AST.",
    url="https://github.com/brianhou/bombast",
    author="Brian Hou",
    packages=["bombast"],
    python_requires="~=3.9",
    entry_points={
        "console_scripts": [
            "bombast=bombast.__init__:main",
        ],
    },
)
