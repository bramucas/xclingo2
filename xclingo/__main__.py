from copyreg import pickle
from typing import Sequence, TextIO
from attr import frozen
from clingo import Control
from xclingo import XclingoControl
from xclingo.preprocessor import (
    DefaultExplainingPipeline,
    ConstraintRelaxerPipeline,
)

from .extensions import load_xclingo_extension
from .utils import FrozenModel, check_options, print_header


def read_files(files: Sequence[TextIO]):
    return "\n".join([file.read() for file in files])


def _init_xclingo_control(
    args,
    program,
    constraints=False,
):
    xclingo_control = XclingoControl(
        [str(args.n[0])],
        n_explanations=str(args.n[1]),
        solving_preprocessor_pipeline=ConstraintRelaxerPipeline() if constraints else None,
    )

    if args.auto_tracing != "none":
        xclingo_control.add_to_explainer(
            "base", [], load_xclingo_extension(f"autotrace_{args.auto_tracing}.lp")
        )

    if args.output == "graph-models":
        xclingo_control.add_to_explainer("base", [], load_xclingo_extension("graph_models_show.lp"))

    if constraints:
        xclingo_control.add_to_explainer(
            "base", [], load_xclingo_extension("violated_constraints_show_trace.lp")
        )
        if args.constraint_explaining == "minimize":
            xclingo_control.add_to_explainer(
                "base", [], load_xclingo_extension("violated_constraints_minimize.lp")
            )

    xclingo_control.add("base", [], program)
    xclingo_control.ground([("base", [])])

    return xclingo_control


def solve_explain(args, xclingo_control: XclingoControl):
    nmodel = 0
    for xmodel in xclingo_control.solve():
        nmodel += 1
        print(f"Answer: {nmodel}")
        print(xmodel)
        nexpl = 0
        for graphModel in xmodel.explain_model():
            nexpl += 1
            print(f"##Explanation: {nmodel}.{nexpl}")
            if args.output == "graph-models":
                print(graphModel)
            else:
                for sym in graphModel.show_trace:
                    e = graphModel.explain(sym)
                    if e is not None:
                        print(e)
        print(f"##Total Explanations:\t{nexpl}")
    if nmodel > 0:
        print(f"Models:\t{nmodel}")
        return False
    else:
        return True


def explain_constraints(args, program):
    print("UNSATISFIABLE")
    print(f"Relaxing constraints... (mode={args.constraint_explaining})")

    xclingo_control = _init_xclingo_control(
        args,
        program,
        constraints=True,
    )

    solve_explain(args, xclingo_control)


def into_pickle(args, xclingo_control: XclingoControl, save_on_unsat=False):
    buf = []
    for xmodel in xclingo_control.solve():
        for graph_model in xmodel.explain_model():
            buf.append(frozenset(str(s) for s in graph_model.symbols(shown=True)))

    if len(buf) == 0 and not save_on_unsat:
        return True

    import pickle

    with open(args.picklefile, "wb") as picklefile:
        pickle.dump(frozenset(buf), picklefile)
        print(f"Results saved as frozen sets at {args.picklefile}")

    return False


def main():
    """Main function. Checks command line arguments and acts in consequence."""
    args = check_options()

    # Prints translation and exits
    if args.output == "translation":
        print(DefaultExplainingPipeline().translate("translation", read_files(args.infiles)))
        return 0

    print_header(args)
    programs = read_files(args.infiles)
    xclingo_control = _init_xclingo_control(args, programs)

    if args.picklefile:  # default value: ""
        unsat = into_pickle(args, xclingo_control, save_on_unsat=False)
        if unsat:
            into_pickle(
                args, _init_xclingo_control(args, programs, constraints=True), save_on_unsat=True
            )
    else:
        unsat = solve_explain(args, xclingo_control)
        if unsat:
            explain_constraints(args, programs)


if __name__ == "__main__":
    main()
