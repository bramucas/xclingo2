from xclingo import Explainer as Explainer
from xclingo import XclingoControl
from xclingo import __version__ as xclingo_version
from argparse import ArgumentParser, FileType
import sys


def check_options():
    # Handles arguments of xclingo
    parser = ArgumentParser(
        description="Tool for explaining (and debugging) ASP programs", prog="xclingo"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="xclingo {version}".format(version=xclingo_version),
        help="Prints the version and exists.",
    )
    optional_group = parser.add_mutually_exclusive_group()
    optional_group = parser.add_argument(
        "--out",
        type=str,
        choices=[
            "ascii-trees",
            "translation",
            "graph-models",
            "clingraph",
            "annotations-translation",
        ],
        default="ascii-trees",
        help="""Determines the format of the output. "translation" will output the translation 
        together with the xclingo logic program. "graph-models" will output the explanation 
        graphs following clingraph format.""",
    )
    parser.add_argument(
        "--auto-tracing",
        type=str,
        choices=["none", "facts", "all"],
        default="none",
        help="Automatically creates traces for the rules of the program. Default: none.",
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


def read_files(files):
    return "\n".join([file.read() for file in files])


def translate(program, auto_trace, graph_models_format):
    explainer = Explainer(auto_trace=auto_trace, graph_models_format=graph_models_format)
    explainer.add("base", [], program)
    explainer._translate_program()
    translation = explainer._preprocessor.get_translation()
    translation += explainer._lp_loader._getExplainerLP()
    return translation


def print_explanation_atoms(xControl: XclingoControl):
    nmodel = 0
    for xmodel in xControl.solve():
        nmodel += 1
        print(f"Answer: {nmodel}")
        print(xmodel)
        nexpl = 0
        for graphModel in xmodel.explain_model():
            nexpl += 1
            print(f"##Explanation: {nexpl}")
            print(graphModel)
        print(f"##Total Explanations:\t{nexpl}")


def print_text_explanations(xControl: XclingoControl):
    nmodel = 0
    for xmodel in xControl.solve():
        nmodel += 1
        print(f"Answer: {nmodel}")
        print(xmodel)
        nexpl = 0
        for graphModel in xmodel.explain_model():
            nexpl += 1
            print(f"##Explanation: {nexpl}")
            for sym in xControl.explainer._show_trace:
                e = graphModel.explain(sym)
                if e is not None:
                    print(e)
        print(f"##Total Explanations:\t{nexpl}")
    print(f"Models:\t{nmodel}")


def print_clingraph_facts(xControl: XclingoControl):
    raise RuntimeError("Not implemented yet")


def main():
    args = check_options()

    if args.out == "annotations-translation":
        program = read_files(args.infiles)
        from xclingo.preprocessor import Preprocessor

        print(Preprocessor.translate_annotations(program))
        return 0
    elif args.out == "translation":
        program = read_files(args.infiles)
        print(
            translate(
                program, args.auto_tracing, "xclingo" if args.out != "clingraph" else "clingraph"
            )
        )
        return 0

    xControl = XclingoControl(
        n_solutions=str(args.n[0]),
        n_explanations=str(args.n[1]),
        auto_trace=args.auto_tracing,
        graph_models_format="xclingo" if args.out != "clingraph" else "clingraph",
    )

    for file in args.infiles:
        xControl.add("base", [], file.read())

    xControl.ground()

    if args.out in {"graph-models", "clingraph"}:
        print_explanation_atoms(xControl)
    elif args.out == "clingraph":
        print_clingraph_facts(xControl)
    else:
        print_text_explanations(xControl)


if __name__ == "__main__":
    main()
