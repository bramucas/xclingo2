from typing import Sequence
from clingo import Model
from clingo.control import Control
from xclingo.explanation import ExplanationGraphModel
from xclingo.explainer import Explainer

from xclingo.preprocessor import PreprocessorPipeline
from xclingo.preprocessor import DefaultExplainingPipeline


class XClingoModel(Model):
    def __init__(self, original_model: Model, explainer: Explainer):
        super().__init__(original_model._rep)
        self._explainer = explainer

    def explain_model(self) -> Sequence[ExplanationGraphModel]:
        return self._explainer._compute_graphs(self)


class XclingoControl:
    """Interface to xclingo pipeline. Grounding, solving, explaining."""

    def __init__(
        self,
        n_solutions: str = "1",
        n_explanations: str = "1",
        pre_solving_pipeline: PreprocessorPipeline = PreprocessorPipeline(),
        pre_explainer_pipeline=None,
        explainer_context=None,
        lp_extensions=[],
    ):
        self.control = Control([n_solutions])
        self.pre_solving_pipeline = pre_solving_pipeline
        self.explainer = Explainer(
            internal_control_arguments=[
                n_explanations,
            ],
            preprocessor_pipe=pre_explainer_pipeline,
            custom_context=explainer_context,
            lp_extensions=lp_extensions,
        )

    def add(self, name: str, parameters: Sequence, program: str):
        """It adds a program to the control.
        Args:
            name (str): name of program block to add.
            program (str): a logic program in ASP format.
        """
        self.control.add(name, parameters, self.pre_solving_pipeline.translate(name, program))
        self.explainer.add(name, program)

    def ground(self, context=None):
        """Ground (only base for now) programs.
        Args:
            context (Object, optional): Context to be passed to the original program control.
            Defaults to None.
        """

        self.control.ground([("base", [])], context)

    def solve(self, on_xclingo_model=None) -> Sequence[XClingoModel]:
        """Returns a generator of xclingo.explanation.Explanation objects. If on_explanation is not None, it is called for each explanation.
        Yields:
            Explation: a tree-like object that represents an explanation.
        """
        with self.control.solve(yield_=True) as solution_iterator:
            for model in solution_iterator:
                yield XClingoModel(model, self.explainer)

    def _default_output(self):
        output = ""
        nanswer = 0
        for xModel in self.solve():
            nanswer += 1
            output += f"Answer: {nanswer}\n"
            output += " ".join(map(str, xModel.symbols(shown=True))) + "\n"
            nexpl = 0
            for graphModel in xModel.explain_model():
                nexpl += 1
                output += f"##Explanation: {nexpl}\n"
                output += "\n".join(
                    [graphModel.explain(s).ascii_tree() for s in self.explainer._show_trace]
                )
                output += "\n"
            output += f"##Total Explanations:\t{nexpl}\n"
        output += f"Models:\t{nanswer}\n"
        return output
