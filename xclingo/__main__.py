from xclingo import Explainer as Explainer
from xclingo import __version__ as xclingo_version
from clingo import Control
from argparse import ArgumentParser, FileType
import sys

def check_options():
    # Handles arguments of xclingo
    parser = ArgumentParser(description='Tool for explaining (and debugging) ASP programs', prog='xclingo')
    parser.add_argument('--version', action='version',
                        version='xclingo {version}'.format(version=xclingo_version),
                        help='Prints the version and exists.')
    optional_group = parser.add_mutually_exclusive_group()
    optional_group.add_argument('--only-translate', action='store_true',
                        help="Prints the internal translation and exits.")
    optional_group.add_argument('--only-translate-annotations', action='store_true',
                        help="Prints the internal translation and exits.")
    optional_group.add_argument('--only-explanation-atoms', action='store_true',
                        help="Prints the atoms used by the explainer to build the explanations.")
    parser.add_argument('--auto-tracing', type=str, choices=["none", "facts", "all"], default="none",
                        help="Automatically creates traces for the rules of the program. Default: none.")
    parser.add_argument('-n', nargs=2, default=(1,1), type=int, help="Number of answer sets and number of desired explanations.")
    parser.add_argument('infiles', nargs='+', type=FileType('r'), default=sys.stdin, help="ASP program")
    return parser.parse_args()

def read_files(files):
    return "\n".join([file.read() for file in files])

def translate(program, auto_trace):
    explainer = Explainer(auto_trace=auto_trace)
    explainer.add('base', [], program)
    explainer._translate_program()
    translation =  explainer._preprocessor.get_translation()
    translation += explainer._getExplainerLP(auto_trace=auto_trace)
    return translation   

def print_explanation_atoms(control, explainer: Explainer):
    with control.solve(yield_=True) as it:
        nanswer=1
        for m in it:
            print(f'Answer {nanswer}')
            print(' '.join([str(sym) for sym in m.symbols(shown=True)]))
            nexpl=1
            for xclingo_m in explainer.get_xclingo_models(m):
                print(f'Explanation: {nexpl}')
                print("\n".join([str(sym) for sym in xclingo_m.symbols(shown=True)]))
                print()
                nexpl+=1
            nanswer+=1

def print_text_explanations(control, explainer:Explainer):
    with control.solve(yield_=True) as it:
        nanswer=1
        for m in it:
            print(f'Answer {nanswer}')
            for e in explainer.explain(m):
                print(e.ascii_tree())
            nanswer+=1

def main():
    args = check_options()

    if args.only_translate_annotations:
        program = read_files(args.infiles)
        from xclingo.preprocessor import Preprocessor
        print(Preprocessor.translate_annotations(program))
        return 0

    if args.only_translate:
        program = read_files(args.infiles)
        print(translate(program, args.auto_tracing))
        return 0

    control = Control([str(args.n[0])])
    explainer = Explainer(
        [
            str(args.n[1]), 
        ], 
        auto_trace=args.auto_tracing
    )

    for file in args.infiles:
        prog = file.read()
        explainer.add(file.name, [], prog)
        control.add("base", [], prog)

    control.ground([("base", [])])

    if args.only_explanation_atoms:
        print_explanation_atoms(control, explainer)
    else:
        print_text_explanations(control, explainer)    

if __name__ == '__main__':
    main()
