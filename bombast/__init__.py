"""bombast obfuscates Python 3 source code by manipulating the AST.

bombast replaces names with a random new identifier, then repeatedly applies
various transformations to the AST.
"""


import argparse
import ast
import json
import random
import sys

from bombast import visitors


def load_config(path, default="bombast.config"):
    if path is None:
        path = default
    try:
        with open(path) as f:
            return json.load(f)
    except IOError as e:
        if path != default:
            raise
    except ValueError as e:
        print("Error:", path, "is an invalid configuration file", file=sys.stderr)
        exit(1)
    return {}


def configure(path):
    options = load_config(path)
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
    preprocess = visitors.Preprocess()
    preprocess.visit(root)

    bombast = visitors.Bombast(preprocess)
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
