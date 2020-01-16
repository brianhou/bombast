from bombast import *

def main():
    parser = argparse.ArgumentParser(description='Obfuscate Python source code.')
    parser.add_argument('infile', type=argparse.FileType('rb'),
                        default=sys.stdin,
                        help='input')
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default='obfuscated.py',
                        help='output [default: obfuscated.py]')
    parser.add_argument('--seed', type=int, default=0,
                        help='random seed [default: 0]')
    parser.add_argument('--iters', type=int, default=1,
                        help='number of iterations [default: 1]')
    parser.add_argument('--config', type=str,
                        help='configuration file [default: bombast.config]')
    parser.add_argument('--show-translations', action='store_true',
                        help='print translations to stdout')
    args = parser.parse_args()
    configure(args.config)

    random.seed(args.seed)
    root = ast.parse(args.infile.read())

    # Choose renamings
    preprocess = Preprocess()
    preprocess.visit(root)

    bombast = Bombast(preprocess)
    for _ in range(args.iters):
        root = bombast.visit(root)

    # Postprocessing
    root.body.sort(key=lambda x: not isinstance(x, ast.Import)) # move imports
    ast.fix_missing_locations(root) # fix AST

    print(astunparse.unparse(root), file=args.outfile)
    if args.show_translations:
        for original, obfuscated in preprocess.mapping.items():
            print(original, '=', obfuscated)


main()
