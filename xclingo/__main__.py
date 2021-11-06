from xclingo import Explainer as Explainer
from clingo import Control
from argparse import ArgumentParser, FileType
import sys


def check_options():
    # Handles arguments of xclingo
    parser = ArgumentParser(description='Tool for explaining (and debugging) ASP programs', prog='xclingo')
    parser.add_argument('--only-translate', action='store_true',
                        help="Prints the internal translation and exits. Default: false.")
    parser.add_argument('--only-translate-comments', action='store_true',
                        help="Prints the internal translation and exits. Default: false.")
    parser.add_argument('--only-explanation-atoms', action='store_true',
                        help="Prints the atoms used by the explainer to build the explanations. Default: false.")
    parser.add_argument('--auto-tracing', type=str, choices=["none", "facts", "all"], default="none",
                        help="Automatically creates traces for the rules of the program. Default: none.")
    parser.add_argument('n', default='1', type=str, help="Number of answer sets.")
    parser.add_argument('nexpl', default='1', type=str, help="Number of explanations for each atom to be explained.")
    parser.add_argument('infiles', nargs='+', type=FileType('r'), default=sys.stdin, help="ASP program")
    return parser.parse_args()

def read_files(files):
    return "".join([file.read() for file in files])

def translate(program, auto_trace):
    explainer = Explainer(auto_trace=auto_trace)
    explainer.add('base', [], program)
    explainer._translate_program()
    translation =  explainer._preprocessor.get_translation()
    translation += explainer._getExplainerLP(auto_trace=auto_trace)
    return translation   

def print_explanation_atoms(control, explainer: Explainer):
    nanswer=1
    with control.solve(yield_=True) as it:
        print(f'Answer {nanswer}')
        for m in it:
            nexpl=1
            for xclingo_m in explainer.get_xclingo_models(m):
                print(f'Explanation: {nexpl}')
                print("\n".join([str(sym) for sym in xclingo_m.symbols(shown=True)]))
                print()
                nexpl+=1
        nanswer+=1

def print_text_explanations(control, explainer:Explainer):
    nanswer=1
    with control.solve(yield_=True) as it:
        print(f'Answer {nanswer}')
        for m in it:
            for e in explainer.explain(m):
                print(e.ascii_tree())
        nanswer+=1

def main():
    args = check_options()
    program = read_files(args.infiles)

    if args.only_translate_comments:
        from xclingo.preprocessor import Preprocessor
        print(Preprocessor.translate_comments(program))
        return 0

    if args.only_translate:
        print(translate(program, args.auto_tracing))
        return 0

    control = Control([args.n])
    explainer = Explainer([args.nexpl], auto_trace=args.auto_tracing)

    explainer.add('base', [], program)
    control.add("base", [], program)
    control.ground([("base", [])])

    if args.only_explanation_atoms:
        print_explanation_atoms(control, explainer)
    else:
        print_text_explanations(control, explainer)    

if __name__ == '__main__':
    main()
