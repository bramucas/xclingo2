from os import read
from typing import Sequence, TextIO
from xclingo import XclingoControl
from xclingo.preprocessor import (
    DefaultExplainingPipeline,
    PreprocessorPipeline,
    ConstraintRelaxerPipeline,
)

from .extensions import ExtensionLoader
from ._args_handler import check_options, print_header


def read_files(files: Sequence[TextIO]):
    """Concats the content of bunch of files into a string.

    Args:
        files (Sequence[TextIO]): A bunch of files.

    Returns:
        str: the concat of all the input files.
    """
    return "\n".join([file.read() for file in files])


def try_solve_explain(args, programs, extension_loader, solving_pipeline=PreprocessorPipeline()):
    xControl = XclingoControl(
        n_solutions=str(args.n[0]),
        n_explanations=str(args.n[1]),
        lp_extensions=extension_loader.get_loaded(),
        pre_solving_pipeline=solving_pipeline,
    )

    xControl.add("base", [], programs)
    xControl.ground()

    unsat = True
    nmodel = 0
    for xmodel in xControl.solve():
        unsat = False
        nmodel += 1
        print(f"Answer: {nmodel}")
        print(xmodel)
        nexpl = 0
        for graphModel in xmodel.explain_model():
            nexpl += 1
            print(f"##Explanation: {nexpl}")
            if args.out == "graph-models":
                print(graphModel)
            else:
                for sym in xControl.explainer._show_trace:
                    e = graphModel.explain(sym)
                    if e is not None:
                        print(e)
        print(f"##Total Explanations:\t{nexpl}")
    print(f"Models:\t{nmodel}")
    return unsat


def main():
    """Main function. Checks command line arguments and acts in consequence."""
    args = check_options()
    print_header(args)

    programs = read_files(args.infiles)
    # Only translate
    if args.out == "translation":
        pipe = DefaultExplainingPipeline()
        print(pipe.translate("translation", programs))
        return 0

    extension_loader = ExtensionLoader()
    if args.auto_tracing != "none":
        extension_loader.loadLPExtension(f"autotrace_{args.auto_tracing}.lp")
    if args.out == "graph-models":
        extension_loader.loadLPExtension("graph_models_show.lp")

    unsat = try_solve_explain(args, programs, extension_loader)

    if unsat:
        print("UNSATISFIABLE")
        print(f"Relaxing constraints... (mode={args.constraint_explaining})")
        # Extensions and pipes for constraints
        extension_loader.loadLPExtension("violated_constraints_show_trace.lp")
        if args.constraint_explaining == "minimize":
            extension_loader.loadLPExtension("violated_constraints_minimize.lp")
        solving_pipeline = ConstraintRelaxerPipeline()
        try_solve_explain(args, programs, extension_loader, solving_pipeline)


if __name__ == "__main__":
    main()
