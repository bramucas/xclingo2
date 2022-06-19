from pdb import set_trace
from typing import Sequence
from clingo import Model, Function, String
from clingo.ast import ProgramBuilder, parse_string
from clingo.control import Control
from xclingo.explanation import ExplanationGraphModel
from xclingo.preprocessor import PreprocessorPipeline, DefaultExplainingPipeline
from ._utils import LPLoader, XClingoContext
from ._logger import XclingoLogger


class Explainer:
    """Xclingo explainer class. Obtains the solutions from an xclingo program and turns them into explanations."""

    def __init__(
        self,
        internal_control_arguments: Sequence[str] = ["1"],
        preprocessor_pipe: PreprocessorPipeline = None,
        custom_context: XClingoContext = None,
        custom_logger=None,
        lp_extensions: Sequence[str] = [],
    ):
        self._internal_control_arguments = internal_control_arguments

        self.preprocessor_pipe = (
            DefaultExplainingPipeline() if preprocessor_pipe is None else preprocessor_pipe
        )
        self.context = XClingoContext() if custom_context is None else custom_context
        self._logger = XclingoLogger() if custom_logger is None else custom_logger

        self.lp_extensions = lp_extensions
        self._lp_loader = LPLoader()
        self._translation = []

    def add(self, name: str, program: str):
        """Adds a program to the explainer."""
        self._translation.append((name, self.preprocessor_pipe.translate(name, program)))

    def _initialize_control(self):
        self._no_labels = False
        project = ["--project=project"]
        return Control(
            self._internal_control_arguments + project,
            logger=self._logger.logger,
        )

    def _ground(self, control: Control, model, context=None):
        """Grounding for the explainer clingo control. It translates the program and adds the original program's model as facts.

        Args:
            control (_type_): _description_
            model (_type_): _description_
            context (_type_, optional): _description_. Defaults to None.
        """
        # Translated original program
        for name, prog in self._translation:
            control.add(name, [], prog)
        # Xclingo core lp
        control.add(name, [], self._lp_loader._loadExplainerLP())
        # Extensions
        for name, extension in self.lp_extensions:
            control.add(name, [], extension)
        # TODO: as assumptions?
        with control.backend() as backend:
            for sym in model.symbols(atoms=True):
                atm_id = backend.add_atom(Function("_xclingo_model", [sym], True))
                backend.add_rule([atm_id], [], False)

        control.ground([("base", [])], context=self.context)

        self._show_trace = [
            s.symbol.arguments[0]
            for s in control.symbolic_atoms.by_signature(name="_xclingo_show_trace", arity=1)
        ]

    def _compute_graphs(self, model: Model, context=None) -> Sequence[ExplanationGraphModel]:
        """Return the Explanations for the given model.

        Args:
            model (Model): original's program model.
            context (Object, optional): context for the explainer program. Defaults to None.

        Returns:
            Iterable[Explanation]: explanations for the given model.
        """
        control = self._initialize_control()
        self._ground(control, model, context)
        self._logger.print_messages()
        with control.solve(yield_=True) as it:
            for graph_model in it:
                yield ExplanationGraphModel(graph_model)
