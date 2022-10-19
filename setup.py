import setuptools

setuptools.setup(
    name="bombast",
    version="v0.3.0",
    description="An obfuscator for Python 3 source code that manipulates the AST.",
    url="https://github.com/brianhou/bombast",
    author="Brian Hou",
    license="MIT",
    classifiers=[
        "Environment :: Console",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    packages=setuptools.find_packages(include=["bombast", "bombast.*"]),
    python_requires="~=3.9",
    entry_points={
        "console_scripts": [
            "bombast=bombast.__init__:main",
        ],
    },
)
