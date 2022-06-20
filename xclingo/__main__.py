from typing import Sequence, TextIO
from xclingo import XclingoControl
from xclingo.preprocessor import (
    DefaultExplainingPipeline,
    ConstraintRelaxerPipeline,
)

from .extensions import load_xclingo_extension
from ._args_handler import check_options, print_header


def read_files(files: Sequence[TextIO]):
    return "\n".join([file.read() for file in files])


def _init_xclingo_control(
    args, solving_preprocessor_pipeline=None, explaining_preprocessor_pipeline=None
):
    xclingo_control = XclingoControl(
        [str(args.n[0])],
        n_explanations=str(args.n[1]),
        solving_preprocessor_pipeline=solving_preprocessor_pipeline,
        explaining_preprocessor_pipeline=explaining_preprocessor_pipeline,
    )

    if args.auto_tracing != "none":
        xclingo_control.add_to_explainer(
            "base", [], load_xclingo_extension(f"autotrace_{args.auto_tracing}.lp")
        )
    if args.out == "graph-models":
        xclingo_control.add_to_explainer("base", [], load_xclingo_extension("graph_models_show.lp"))

    programs = read_files(args.infiles)
    xclingo_control.add("base", [], programs)
    xclingo_control.ground([("base", [])])

    return xclingo_control


def solve_explain(args, xclingo_control):
    unsat = True
    nmodel = 0
    for xmodel in xclingo_control.solve():
        unsat = False
        nmodel += 1
        print(f"Answer: {nmodel}")
        print(xmodel)
        nexpl = 0
        for graphModel in xmodel.explain_model():
            nexpl += 1
            print(f"##Explanation: {nmodel}.{nexpl}")
            if args.out == "graph-models":
                print(graphModel)
            else:
                for sym in graphModel.show_trace:
                    e = graphModel.explain(sym)
                    if e is not None:
                        print(e)
        print(f"##Total Explanations:\t{nexpl}")
    print(f"Models:\t{nmodel}")
    return unsat


def main():
    """Main function. Checks command line arguments and acts in consequence."""
    args = check_options()

    # Prints translation and exits
    if args.out == "translation":
        print(DefaultExplainingPipeline().translate("translation", read_files(args.infiles)))
        return 0

    print_header(args)

    xclingo_control = _init_xclingo_control(args)

    unsat = solve_explain(args, xclingo_control)
    if unsat:
        print("UNSATISFIABLE")
        print(f"Relaxing constraints... (mode={args.constraint_explaining})")

        xclingo_control = _init_xclingo_control(
            args, solving_preprocessor_pipeline=ConstraintRelaxerPipeline()
        )
        # Extensions for constraint explaining
        xclingo_control.add_to_explainer(
            load_xclingo_extension("violated_constraints_show_trace.lp")
        )
        if args.constraint_explaining == "minimize":
            xclingo_control.add_to_explainer(
                load_xclingo_extension("violated_constraints_minimize.lp")
            )

        solve_explain(args, xclingo_control)


if __name__ == "__main__":
    main()
