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
        print(f"Error: {path} is an invalid configuration file", file=sys.stderr)
        exit(1)
    return {}


def configure(path):
    known_options = {"ignore_names"}
    listed_options = load_config(path)
    configured = {}
    for option, value in listed_options.items():
        if option not in known_options:
            print(f"Warning: {option=} is unused.", file=sys.stderr)
            continue
        configured[option] = value
    return configured


def main():
    parser = argparse.ArgumentParser(description="Obfuscate Python source code.")
    parser.add_argument(
        "infile",
        type=argparse.FileType("r"),
        default=sys.stdin,
        help="input",
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
    options = configure(args.config)

    random.seed(args.seed)
    root = ast.parse(args.infile.read())
    args.infile.close()

    # Choose renamings
    preprocess = visitors.Preprocess(**options)
    preprocess.visit(root)

    # Apply transformations
    bombast = visitors.Bombast(preprocess, **options)
    for _ in range(args.iters):
        root = bombast.visit(root)

    # Postprocessing: move imports and fix AST
    root.body.sort(key=lambda x: not isinstance(x, ast.Import))
    ast.fix_missing_locations(root)

    print(ast.unparse(root), file=args.outfile)
    args.outfile.close()

    if args.show_translations:
        for original, obfuscated in preprocess.mapping.items():
            print(original, "=", obfuscated)


if __name__ == "__main__":
    main()
