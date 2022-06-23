from clingo import Symbol
from typing import Sequence, Union, Tuple
from clingo import Model, Logger
from clingo.control import Control
from xclingo.explanation import ExplanationGraphModel
from xclingo.explainer import Explainer
from xclingo.explainer._utils import XClingoContext

from xclingo.preprocessor import PreprocessorPipeline
from xclingo.preprocessor import DefaultExplainingPipeline

from xclingo.explainer._logger import XclingoLogger

from ._version import __version__ as xclingo_version


class XClingoModel(Model):
    def __init__(self, original_model: Model, explainer: Explainer):
        super().__init__(original_model._rep)
        self._explainer = explainer

    def explain_model(self) -> Sequence[ExplanationGraphModel]:
        return self._explainer._compute_graphs(self, context=XClingoContext())


class XclingoControl(Control):
    """Interface to xclingo pipeline. Grounding, solving, explaining."""

    def __init__(
        self,
        arguments: Sequence[str] = [],
        logger: Union[Logger, None] = None,
        message_limit: int = 20,
        n_explanations: str = "1",
        solving_preprocessor_pipeline: PreprocessorPipeline = None,
        explaining_preprocessor_pipeline: PreprocessorPipeline = None,
    ):
        # Solver control
        super().__init__(arguments=arguments, logger=logger, message_limit=message_limit)
        self.pre_solving_pipeline = (
            PreprocessorPipeline()
            if solving_preprocessor_pipeline is None
            else solving_preprocessor_pipeline
        )

        # Explainer control
        self.pre_explaining_pipeline = (
            DefaultExplainingPipeline()
            if explaining_preprocessor_pipeline is None
            else explaining_preprocessor_pipeline
        )
        self.expl_logger = XclingoLogger()
        constants = []
        for i, a in enumerate(arguments):
            if a in ("-c", "--const"):
                constants.extend(arguments[i : i + 2])
        self.explainer = Explainer([n_explanations] + constants, logger=self.expl_logger.logger)

    def add(self, name: str, parameters: Sequence[str], program: str) -> None:
        """It adds a program to the control.
        Args:
            name (str): name of program block to add.
            program (str): a logic program in ASP format.
        """
        super().add(name, parameters, self.pre_solving_pipeline.translate(name, program))
        self.explainer.add(name, parameters, self.pre_explaining_pipeline.translate(name, program))

    def extend_explainer(self, name: str, parameters: Sequence[str], program: str) -> None:
        self.explainer.add(name, parameters, program)

    def add_show_trace(self, atom: Symbol, conditions: Sequence[Tuple[bool, Symbol]] = []):
        rule = "_xclingo_show_trace({atom}) :- _xclingo_model({atom}), {body}.".format(
            atom=str(atom),
            body=",".join(f"{'' if sign else 'not'} {str(s)}" for sign, s in conditions),
        )
        self.explainer.add("base", [], f"_xclingo_show_trace({str(atom)}) :- .")

    def solve(self, on_unsat=None) -> Sequence[XClingoModel]:
        """Returns a generator of xclingo.explanation.Explanation objects. If on_explanation is not None, it is called for each explanation."""
        if on_unsat:
            super().solve(on_unsat=on_unsat)
        with super().solve(yield_=True) as solution_iterator:
            for model in solution_iterator:
                yield XClingoModel(model, self.explainer)

    def _default_output(self) -> None:
        output = ""
        nanswer = 0
        for xModel in self.solve():
            nanswer += 1
            output += f"Answer: {nanswer}\n"
            output += " ".join(map(str, xModel.symbols(shown=True))) + "\n"
            nexpl = 0
            for graphModel in xModel.explain_model():
                nexpl += 1
                output += f"##Explanation: {nanswer}.{nexpl}\n"
                output += "\n".join(
                    [graphModel.explain(s).ascii_tree() for s in graphModel.show_trace]
                )
                output += "\n"
            output += f"##Total Explanations:\t{nexpl}\n"
        output += f"Models:\t{nanswer}\n"
        return output
