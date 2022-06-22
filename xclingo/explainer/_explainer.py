from typing import Iterator, Sequence, Union
from clingo import Logger, Model, Function
from clingo.control import Control
from xclingo.explanation import ExplanationGraphModel
from xclingo.xclingo_lp import FIRED_LP, GRAPH_LP, SHOW_LP
from ._utils import XClingoContext


class Explainer:
    """Xclingo explainer class. Obtains the solutions from an xclingo program and turns them into explanations."""

    def __init__(
        self,
        arguments: Sequence[str] = [],
        logger: Union[Logger, None] = None,
        message_limit: int = 20,
    ):
        self.arguments = arguments
        self.logger = logger
        self.message_limit = message_limit

        self.programs = []

    def add(self, name, parameters, program):
        self.programs.append((name, parameters, program))

    def _compute_graphs(
        self, model: Model, on_explanation=None, context=None
    ) -> Iterator[ExplanationGraphModel]:
        """Return the ExplanationGraphModel instances for the given (original's program) model.

        Args:
            model (Model): original's program model.
            context (_type_, optional): Context class for the internal Control instance. Defaults to None.

        Yields:
            ExplanationGraphModel: each explanation for the model.
        """
        # Initializes control
        ctl = Control(
            arguments=self.arguments + ["--project=project"],
            logger=self.logger,
            message_limit=self.message_limit,
        )
        # Adds xclingo program
        ctl.add("base", [], FIRED_LP)
        ctl.add("base", [], GRAPH_LP)
        ctl.add("base", [], SHOW_LP)
        # Translations and extensions
        for name, parameters, program in self.programs:
            ctl.add(name, parameters, program)
        # Adds model (TODO: is it possible to do this with just one control?)
        with ctl.backend() as back:
            for sym in model.symbols(atoms=True):
                back.add_rule([back.add_atom(Function("_xclingo_model", [sym], True))], [], False)
        # Ground
        ctl.ground([("base", [])], context=context if context is not None else XClingoContext())
        # Solve
        if on_explanation is not None:
            ctl.solve(on_model=on_explanation)
        else:
            with ctl.solve(yield_=True) as it:
                for graph_model in it:
                    yield ExplanationGraphModel(graph_model)
