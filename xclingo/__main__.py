import sys
from argparse import ArgumentParser, FileType
from typing import Iterable, TextIO
from xclingo import Explainer
from xclingo import XclingoControl
from xclingo import __version__ as xclingo_version
from xclingo.preprocessor import Preprocessor


def check_options():
    """Handles arguments of xclingo"""
    parser = ArgumentParser(
        description="Tool for explaining (and debugging) ASP programs", prog="xclingo"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"xclingo {xclingo_version}",
        help="Prints the version and exists.",
    )
    optional_group = parser.add_mutually_exclusive_group()
    optional_group.add_argument(
        "--only-translate", action="store_true", help="Prints the internal translation and exits."
    )
    optional_group.add_argument(
        "--only-translate-annotations",
        action="store_true",
        help="Prints the internal translation and exits.",
    )
    optional_group.add_argument(
        "--only-explanation-atoms",
        action="store_true",
        help="Prints the atoms used by the explainer to build the explanations.",
    )
    parser.add_argument(
        "--auto-tracing",
        type=str,
        choices=["none", "facts", "all"],
        default="none",
        help="""Automatically creates traces for the rules of the program. Default: none.
        - 'facts' will create labels for every fact rule in the program.
        - 'all' will create labels for every rule in the program.""",
    )
    parser.add_argument(
        "--constraint-explaining",
        type=str,
        choices=["unsat", "minimize", "all"],
        default="unsat",
        help="""Explains traced constraints of the program. Default: unsat.
        - 'unsat' will only explain constraints if original program is UNSAT. In such a case
        the ocurrence of violated constraints will be minimized when solving the original program.
        - 'minimize' acts as 'unsat' but the first UNSAT check is skipped. Directly minimizes the
        constraints when solving the original program. Useful when the original program is known
        UNSAT but it takes long to check it.
        - 'all' will explain all constraints and will not minimize them before explaining.""",
    )
    parser.add_argument(
        "-n",
        nargs=2,
        default=(1, 1),
        type=int,
        help="Number of answer sets and number of desired explanations.",
    )
    parser.add_argument(
        "infiles", nargs="+", type=FileType("r"), default=sys.stdin, help="ASP program"
    )
    return parser.parse_args()


def read_files(files: Iterable[TextIO]):
    """Concats the content of bunch of files into a string.

    Args:
        files (Iterable[TextIO]): A bunch of files.

    Returns:
        str: the concat of all the input files.
    """
    return "\n".join([file.read() for file in files])


def translate(program: str, auto_trace: str):
    """Returns the xclingo translation for the given program.

    Args:
        program (str): asp program to be translated.
        auto_trace (str): ['none', 'facts', 'all'] auto trace mode. 'facts' mode will create labels
        for every fact rule in the program. 'all' will create labels for every rule in the program.

    Returns:
        _type_: _description_
    """
    explainer = Explainer(auto_trace=auto_trace)
    explainer.add("base", [], program)
    explainer._translate_program()
    translation = explainer._preprocessor.get_translation()
    translation += explainer._get_explainer_lp(auto_trace=auto_trace)
    return translation


def print_explanation_atoms(x_control: XclingoControl):
    """Obtains and prints the solutions of the xclingo program. This is, the explanation graphs as
    ASP facts

    Args:
        xControl (XclingoControl): control object. The program must have been added and grounded
        before.
    """
    n = 0
    for xmodel in x_control.get_xclingo_models():
        n += 1
        print(f"Answer {n}")
        print(xmodel)


def print_text_explanations(x_control: XclingoControl):
    """Obtains and prints the explanations of the program.

    Args:
        xControl (XclingoControl): control object. The program must have been added and grounded
        before.
    """
    n = 0
    for answer in x_control.explain():
        n += 1
        print(f"Answer {n}")
        for expl in answer:
            print(expl.ascii_tree())


def main():
    """Main function. Checks command line arguments and acts in consequence."""
    args = check_options()

    if args.only_translate_annotations:
        program = read_files(args.infiles)
        print(Preprocessor._translate_annotations(program))
        return 0

    if args.only_translate:
        program = read_files(args.infiles)
        print(translate(program, args.auto_tracing))
        return 0

    x_control = XclingoControl(
        n_solutions=str(args.n[0]),
        n_explanations=str(args.n[1]),
        auto_trace=args.auto_tracing,
        constraint_explaining=args.constraint_explaining,
    )

    for file in args.infiles:
        x_control.add("base", [], file.read())

    x_control.ground()

    if args.only_explanation_atoms:
        print_explanation_atoms(x_control)
    else:
        print_text_explanations(x_control)


if __name__ == "__main__":
    main()
