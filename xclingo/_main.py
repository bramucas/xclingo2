from typing import Union, Sequence
from clingo import Model, Function, String, Symbol
from clingo.ast import ProgramBuilder, parse_string
from clingo.control import Control
from clingo.symbol import SymbolType
from pyrsistent import s
from xclingo.explanation import Explanation, ExplanationGraphModel
from xclingo.preprocessor import Preprocessor, ConstraintRelaxer

from clingo.core import MessageCode


class Context:
    """Xclingo context class."""

    def label(self, text, tup):
        """Given the text of a label and a tuple of symbols, handles the variable instantiation
        and returns the processed text label."""
        if text.type == SymbolType.String:
            text = text.string
        else:
            text = str(text).strip('"')
        for val in tup.arguments:
            text = text.replace("%", val.string if val.type == SymbolType.String else str(val), 1)
        return [String(text)]

    def inbody(self, body):
        """Handles the inbody/2 predicate from the xclingo_lp program."""
        if len(body.arguments) > 0:
            return [
                Function(
                    "",
                    [a, body],
                    True,
                )
                for a in body.arguments
            ]
        else:
            return Function("empty", [], True)


class LPLoader:
    def __init__(self, auto_trace: str = "none", graphs: str = "xclingo"):
        self.auto_trace = auto_trace
        self.graphs = graphs

    def _getExplainerLP(self):
        if hasattr(self, "_explainerLP") == False:
            setattr(self, "_explainerLP", self._loadExplainerLP())
        return self._explainerLP

    def _loadExplainerLP(self):
        try:
            import importlib.resources as pkg_resources
        except ImportError:
            # Try backported to PY<37 `importlib_resources`.
            import importlib_resources as pkg_resources

        from . import xclingo_lp

        program = ""
        program += pkg_resources.read_text(xclingo_lp, "xclingo_fired.lp")
        program += pkg_resources.read_text(xclingo_lp, "xclingo_graph.lp")
        if self.graphs == "xclingo":
            program += pkg_resources.read_text(xclingo_lp, "xclingo_show.lp")
        elif self.graphs == "clingraph":
            program += pkg_resources.read_text(xclingo_lp, "clingraph_graphs.lp")
            program += pkg_resources.read_text(xclingo_lp, "clingraph_show.lp")

        # auto-tracing
        if self.auto_trace == "all":
            program += pkg_resources.read_text(xclingo_lp, "autotrace_all.lp")
        elif self.auto_trace == "facts":
            program += pkg_resources.read_text(xclingo_lp, "autotrace_facts.lp")

        # constraints
        program += pkg_resources.read_text(xclingo_lp, "violated_constraints_show_trace.lp")
        return program


class Explainer:
    """Xclingo explainer class. Obtains the solutions from an xclingo program and turns them into explanations."""

    def __init__(
        self, internal_control_arguments=["1"], auto_trace="none", graph_models_format="xclingo"
    ):
        self._preprocessor = Preprocessor()
        self._memory = []

        self._internal_control_arguments = internal_control_arguments
        self._auto_trace = auto_trace
        self._graph_models_format = graph_models_format
        self._translated = False
        self._current_model = []

        self._show_trace = []

        self._no_labels = False

        self._lp_loader = LPLoader(auto_trace=auto_trace, graphs=graph_models_format)

    def logger(self, _code, msg):
        """Logger TODO: more detail."""
        if _code == MessageCode.AtomUndefined:
            if "xclingo_muted" in msg:
                return
            if "_xclingo_label" in msg:
                self._no_labels = True
                return
            if "_xclingo_show_trace" in msg:
                self._no_show_trace = True
        print(msg)

    def print_messages(self):
        """Prints messages from the logger."""
        if self._no_labels:
            print("xclingo info: any atom or rule has been labelled.")
        if self._show_trace == []:
            print("xclingo info: any atom has been affected by a %!show_trace annotation.")

    def add(self, program_name: str, parameters: Sequence[str], program: str):
        """Adds a program to the explainer."""
        self._memory.append((program_name, program))

    def _initialize_control(self):
        self._no_labels = False
        project = ["--project=project"] if self._graph_models_format == "xclingo" else []
        return Control(
            self._internal_control_arguments + project,
            logger=self.logger,
        )

    def _translate_program(self):
        """Translates the program to the explainer logic program."""
        self._preprocessor._rule_count = 1
        for name, program in self._memory:
            self._preprocessor.translate_program(program, name=name)

    def _ground(self, control: Control, model, context=None):
        """Grounding for the explainer clingo control. It translates the program and adds the original program's model as facts.

        Args:
            control (_type_): _description_
            model (_type_): _description_
            context (_type_, optional): _description_. Defaults to None.
        """
        # Translates the original program
        if not self._translated:
            self._translate_program()

        #
        with ProgramBuilder(control) as builder:
            parse_string(
                self._lp_loader._getExplainerLP() + self._preprocessor.get_translation(),
                lambda ast: builder.add(ast),
            )

        # TODO: as externals?
        with control.backend() as backend:
            for sym in model.symbols(atoms=True):
                atm_id = backend.add_atom(Function("_xclingo_model", [sym], True))
                backend.add_rule([atm_id], [], False)

        control.ground([("base", [])], context=context if context is not None else Context())

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
        self.print_messages()
        with control.solve(yield_=True) as it:
            for graph_model in it:
                yield ExplanationGraphModel(graph_model)


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
        n_solutions="1",
        n_explanations="1",
        auto_trace="none",
        graph_models_format="xclingo",
        constraint_explaining="unsat",
    ):
        self.n_solutions = n_solutions
        self.n_explanations = n_explanations

        self._constraint_explaining = constraint_explaining

        self.control = Control([n_solutions if type(n_solutions) == str else str(n_solutions)])
        self.explainer = Explainer(
            [
                n_explanations if type(n_explanations) == str else str(n_explanations),
            ],
            auto_trace=auto_trace,
            graph_models_format=graph_models_format,
        )
        self._explainer_context = None

        self.program_memory = []

    @staticmethod
    def _init_control(n_solutions: int):
        """Initializes a control.

        Args:
            n_solutions (int): number of solutions

        Returns:
            Control: clingo control for the original program.
        """
        return Control([str(n_solutions)])

    def add(self, name, parameters, program):
        """It adds a program to the control.

        Args:
            name (str): name of program block to add.
            parameters (Sequence[str]): a list (or Sequence) of for the program.
            program (str): a logic program in ASP format.
        """
        if self._constraint_explaining != "unsat":
            constraint_relaxer = ConstraintRelaxer()
            constraint_relaxer.preprocess(program)
            self.control.add("base", parameters, constraint_relaxer.get_translation())
        else:
            self.control.add("base", parameters, program)
        self.explainer.add(name, [], program)

        self.program_memory.append((name, program))

    def ground(self, context=None):
        """Ground (only base for now) programs.

        Args:
            context (Object, optional): Context to be passed to the original program control.
            Defaults to None.
        """
        self.control.ground([("base", [])], context)

    def _solve_original(self, minimize: bool):
        if minimize:
            with self.control.backend() as backend:
                atoms_to_minimize = []
                for sym in self.control.symbolic_atoms:
                    if (
                        sym.symbol.name == "_xclingo_violated_constraint"
                        and len(sym.symbol.arguments) == 2
                    ):
                        atoms_to_minimize.append((sym.literal, 1))
                backend.add_minimize(0, atoms_to_minimize)

        return self.control.solve(yield_=True)

    def solve(self) -> Sequence[XClingoModel]:
        """Returns a generator of xclingo.explanation.Explanation objects. If on_explanation is not None, it is called for each explanation.

        Args:
            on_explanation (Callable, optional): callable that will be called for each Explanation, it must receive Explanation as a parameter. Defaults to None.

        Yields:
            Explation: a tree-like object that represents an explanation.
        """
        unsat = True
        with self._solve_original(
            minimize=(self._constraint_explaining == "minimize")
        ) as solution_iterator:
            for model in solution_iterator:
                unsat = False
                yield XClingoModel(model, self.explainer)

        if unsat:
            # resets control but relax constraints
            self.control = self._init_control(self.n_solutions)
            for name, program in self.program_memory:
                constraint_relaxer = ConstraintRelaxer()
                constraint_relaxer.preprocess(program)
                self.control.add(name, [], constraint_relaxer.get_translation())
            self.ground()

            with self._solve_original(minimize=True) as solution_iterator:
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
