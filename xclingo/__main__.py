from typing import Sequence, TextIO
from xclingo import XclingoControl
from xclingo.preprocessor import (
    DefaultExplainingPipeline,
    ConstraintRelaxerPipeline,
    ConstraintExplainingPipeline,
)
from xclingo.extensions import load_xclingo_extension
from xclingo.error import ModelControlGroundingError, ModelControlParsingError
from xclingo.explainer.error import ExplanationControlParsingError, ExplanationControlGroundingError
from ._utils import print_header, print_version
from ._arguments_handler import check_options

from clingraph.orm import Factbase
from clingraph import compute_graphs as compute_clingraphs
from clingraph.graphviz import render


def read_files(files: Sequence[TextIO]):
    return "\n".join([file.read() for file in files])


def _init_xclingo_control(
    args,
    unknown_args,
    program,
    constraints=False,
):
    xclingo_control = XclingoControl(
        [str(args.n[0])] + unknown_args,
        n_explanations=str(args.n[1]),
        solving_preprocessor_pipeline=ConstraintRelaxerPipeline() if constraints else None,
        explaining_preprocessor_pipeline=ConstraintExplainingPipeline() if constraints else None,
    )

    if args.auto_tracing != "none":
        xclingo_control.extend_explainer(
            "base", [], load_xclingo_extension(f"autotrace_{args.auto_tracing}.lp")
        )

    if args.output == "render-graphs":
        xclingo_control.extend_explainer("base", [], load_xclingo_extension("graph_locals.lp"))
        xclingo_control.extend_explainer("base", [], load_xclingo_extension("graph_styles.lp"))

    if constraints:
        xclingo_control.extend_explainer(
            "base", [], load_xclingo_extension("violated_constraints_show_trace.lp")
        )
        if args.constraint_explaining == "minimize":
            xclingo_control.extend_explainer(
                "base", [], load_xclingo_extension("violated_constraints_minimize.lp")
            )

    xclingo_control.add("base", [], program)
    xclingo_control.ground([("base", [])])

    return xclingo_control


def print_explainer_program(args):
    from xclingo.xclingo_lp import FIRED_LP, GRAPH_LP, SHOW_LP

    print_version()
    print(FIRED_LP)
    print(GRAPH_LP)
    print(SHOW_LP)

    if args.auto_tracing != "none":
        print(load_xclingo_extension(f"autotrace_{args.auto_tracing}.lp"))

    if args.output == "render-graphs":
        print(load_xclingo_extension("graph_locals.lp"))
        print(load_xclingo_extension("graph_styles.lp"))

    if args.debug_output == "explainer-program":
        pipe = DefaultExplainingPipeline()
    elif args.debug_output == "unsat-explainer-program":
        pipe = ConstraintExplainingPipeline()
    elif args.debug_output == "unsat-solver-program":
        pipe = ConstraintRelaxerPipeline()

    if len(args.infiles) > 0:
        print(pipe.translate("translation", read_files(args.infiles)))


def render_graphs(args, xclingo_control: XclingoControl):
    nmodel = 0
    for x_model in xclingo_control.solve():
        nmodel += 1
        nexpl = 0
        for graph_model in x_model.explain_model():
            nexpl += 1
            render(
                compute_clingraphs(
                    Factbase.from_model(
                        graph_model, prefix="_xclingo_", default_graph="explanation"
                    ),
                    graphviz_type="digraph",
                ),
                name_format=f"explanation{nmodel}-{nexpl}" + "_{graph_name}",
                format="png",
                directory=args.outdir if args.outdir else "out/",
            )

    if nmodel > 0:
        print("Images saved in ./out/")

    return nmodel == 0


def solve_explain(args, xclingo_control: XclingoControl):
    nmodel = 0
    for x_model in xclingo_control.solve():
        nmodel += 1
        print(f"Answer: {nmodel}")
        if args.print_models:
            print(x_model)
        nexpl = 0
        for graph_model in x_model.explain_model():
            nexpl += 1
            print(f"##Explanation: {nmodel}.{nexpl}")
            if args.output == "graph-models":
                print(graph_model)
            else:
                for sym in graph_model.show_trace:
                    e = graph_model.explain(sym)
                    if e is not None:
                        print(e)
        print(f"##Total Explanations:\t{nexpl}")
    if nmodel > 0:
        print(f"Models:\t{nmodel}")
        return False
    else:
        return True


def into_pickle(args, xclingo_control: XclingoControl, save_on_unsat=False):
    buf = []
    for x_model in xclingo_control.solve():
        for graph_model in x_model.explain_model():
            buf.append(frozenset(str(s) for s in graph_model.symbols(shown=True)))

    if len(buf) == 0 and not save_on_unsat:
        return True

    import pickle

    with open(args.picklefile, "wb") as picklefile:
        pickle.dump(frozenset(buf), picklefile)
        print(f"Results saved as frozen sets at {args.picklefile}")

    return False


def ground_solve_explain(args, unknown_args, programs):

    xclingo_control = _init_xclingo_control(args, unknown_args, programs)
    if args.picklefile:  # default value: ""
        unsat = into_pickle(args, xclingo_control, save_on_unsat=False)
    elif args.output == "render-graphs":
        unsat = render_graphs(args, xclingo_control)
    else:
        unsat = solve_explain(args, xclingo_control)

    xclingo_control = _init_xclingo_control(args, unknown_args, programs, constraints=True)
    if unsat:
        if args.picklefile:
            into_pickle(args, xclingo_control, save_on_unsat=True)
        elif args.output == "render-graphs":
            render_graphs(args, xclingo_control)
        else:
            print("UNSATISFIABLE")
            print(f"Relaxing constraints... (mode={args.constraint_explaining})")
            solve_explain(args, xclingo_control)


def main():
    """Main function. Checks command line arguments and acts in consequence."""
    args, unknown_args = check_options()

    # Prints translation and explainer lp and exits
    if args.debug_output != "none":
        print_explainer_program(args)
        return 0

    # Prints translation and exits
    if args.output == "translation":
        print(DefaultExplainingPipeline().translate("translation", read_files(args.infiles)))
        return 0

    print_header(args)
    programs = read_files(args.infiles)

    try:
        ground_solve_explain(args, unknown_args, programs)
    except ModelControlParsingError as e:
        print("*** ERROR: (clingo, original program)", e)
        exit(1)
    except ModelControlGroundingError as e:
        print("*** ERROR: (clingo, original program)", e)
        exit(1)
    except ExplanationControlParsingError as e:
        print("*** ERROR: (xclingo, explainer program)", e)
    except ExplanationControlGroundingError as e:
        print("*** ERROR: (xclingo, explainer program)", e)


if __name__ == "__main__":
    main()
