from xclingo import Explainer as Explainer
from clingo import Control
from argparse import ArgumentParser, FileType
import sys


def check_options():
    # Handles arguments of xclingo
    parser = ArgumentParser(description='Tool for explaining (and debugging) ASP programs', prog='xclingo')
    # parser.add_argument('--debug-level', type=str, choices=["none", "magic-comments", "translation", "causes"], default="none",
    #                     help="Points out the debugging level. Default: none.")
    # parser.add_argument('--auto-tracing', type=str, choices=["none", "facts", "all"], default="none",
    #                     help="Automatically creates traces for the rules of the program. Default: none.")
    parser.add_argument('n', default='1', type=str, help="Number of answer sets.")
    parser.add_argument('nexpl', default='1', type=str, help="Number of explanations for each atom to be explained.")
    parser.add_argument('infiles', nargs='+', type=FileType('r'), default=sys.stdin, help="ASP program")
    return parser.parse_args()

def read_files(files):
    return "".join([file.read() for file in files])

def main():
    args = check_options()
    program = read_files(args.infiles)

    control = Control([args.n])
    explainer = Explainer([args.nexpl])

    explainer.add('base', [], program)
    control.add("base", [], program)
    control.ground([("base", [])])

    nanswer=1
    with control.solve(yield_=True) as it:
        print(f'Answer {nanswer}')
        for m in it:
            explainer.explain(m)
        nanswer+=1

if __name__ == '__main__':
    main()
