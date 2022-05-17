from typing import Iterable, Sequence
from clingo import Model, Function, String
from clingo.ast import ProgramBuilder, parse_string
from clingo.control import Control
from clingo.symbol import SymbolType
from xclingo.explanation import Explanation
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


class Explainer:
    """Xclingo explainer class. Obtains the solutions from an xclingo program and turns them into explanations."""

    def __init__(self, internal_control_arguments=["1"], auto_trace="none"):
        self._preprocessor = Preprocessor()
        self._memory = []

        self._internal_control_arguments = internal_control_arguments
        self._auto_trace = auto_trace
        self._translated = False
        self._current_model = []

        self._no_labels = False
        self._no_show_trace = False

    def logger(self, _code, msg):
        """Logger TODO: more detail."""
        if _code == MessageCode.AtomUndefined:
            if "xclingo_muted(Cause)" in msg:
                return
            if "_xclingo_label_tree/3" in msg:
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
        if self._no_show_trace:
            print("xclingo info: any atom has been affected by a %!show_trace annotation.")

    def clean_log(self):
        """Cleans the logger."""
        self._no_labels = False
        self._no_show_trace = False

    def _get_explainer_lp(self, auto_trace="none"):
        """Returns the explainer logic program."""
        if hasattr(self, "_explainer_lp") is False:
            setattr(self, "_explainer_lp", self._load_explainer_lp(auto_trace))
        return self._explainer_lp

    def _load_explainer_lp(self, auto_trace="none"):
        """Handles the loading of the different modules of the explainer logic program. Then return all together."""
        try:
            import importlib.resources as pkg_resources
        except ImportError:
            # Try backported to PY<37 `importlib_resources`.
            import importlib_resources as pkg_resources

        from . import xclingo_lp  # relative-import the *package* containing the templates

        program = pkg_resources.read_text(xclingo_lp, "xclingo.lp")
        program += pkg_resources.read_text(xclingo_lp, "violated_constraints_show.lp")
        if auto_trace == "all":
            program += pkg_resources.read_text(xclingo_lp, "autotrace_all.lp")
        elif auto_trace == "facts":
            program += pkg_resources.read_text(xclingo_lp, "autotrace_facts.lp")
        return program

    def add(self, program_name: str, parameters: Iterable[str], program: str):
        """Adds a program to the explainer."""
        self._memory.append((program_name, program))

    def _initialize_control(self):
        """Initializes the explainer clingo control."""
        return Control(self._internal_control_arguments + ["--project=project"], logger=self.logger)

    def _translate_program(self):
        """Translates the program to the explainer logic program."""
        self._preprocessor._rule_count = 1
        for name, program in self._memory:
            self._preprocessor.translate_program(program, name=name)

    def _ground(self, control, model, context=None):
        """Grounding for the explainer clingo control. It translates the program and adds the original program's model as facts.

        Args:
            control (_type_): _description_
            model (_type_): _description_
            context (_type_, optional): _description_. Defaults to None.
        """
        if not self._translated:
            self._translate_program()
            self._translated

        with ProgramBuilder(control) as builder:
            parse_string(
                self._get_explainer_lp(auto_trace=self._auto_trace)
                + self._preprocessor.get_translation(),
                lambda ast: builder.add(ast),
            )

        with control.backend() as backend:
            for sym in model.symbols(atoms=True):
                atm_id = backend.add_atom(Function("_xclingo_model", [sym], True))
                backend.add_rule([atm_id], [], False)

        if context is None:
            context = Context()

        control.ground([("base", [])], context=context)

    def _get_explanations(self, control):
        with control.solve(yield_=True) as it:
            for expl_model in it:
                syms = expl_model.symbols(
                    shown=True
                )  # shown is True because we want to get only the summarized graph
                if len(syms) > 0:
                    yield Explanation.from_model(syms)

    def _get_models(self, control):
        with control.solve(yield_=True) as it:
            for expl_model in it:
                yield expl_model

    def get_xclingo_models(self, model: Model) -> Iterable[Model]:
        """Return the models from the xclingo program for a given original program's model.

        Args:
            model (Model): original's program model.

        Returns:
            Iterable[Model]: models from the xclingo program for the given model.
        """
        control = self._initialize_control()
        self.clean_log()
        self._ground(control, model)
        self.print_messages()
        return self._get_models(control)

    def explain(self, model: Model, context=None) -> Iterable[Explanation]:
        """Return the Explanations for the given model.

        Args:
            model (Model): original's program model.
            context (Object, optional): context for the explainer program. Defaults to None.

        Returns:
            Iterable[Explanation]: explanations for the given model.
        """
        control = self._initialize_control()
        self.clean_log()
        self._ground(control, model, context)
        self.print_messages()
        return self._get_explanations(control)


class XclingoControl:
    """Interface to xclingo pipeline. Grounding, solving, explaining."""

    def __init__(
        self, n_solutions="1", n_explanations="1", auto_trace="none", constraint_explaining="unsat"
    ):
        self.n_solutions = n_solutions
        self.n_explanations = n_explanations

        self.control = self._init_control(n_solutions)
        self._constraint_explaining = constraint_explaining

        self.explainer = Explainer(
            [
                n_explanations if isinstance(n_explanations, str) else str(n_explanations),
            ],
            auto_trace=auto_trace,
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
            parameters (Iterable[str]): a list (or iterable) of for the program.
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

    def get_xclingo_models(self):
        """Returns the clingo.Model objects of the explainer, this is the models which represent
        the explanations.

        Returns:
            Generator[cilngo.Model]: a generator of clingo.Model objects.
        """
        with self.control.solve(yield_=True) as solution_iterator:
            for model in solution_iterator:
                return self.explainer.get_xclingo_models(model)

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

    def explain(self, on_explanation=None):
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
                if on_explanation is None:
                    yield self.explainer.explain(model, context=self._explainer_context)
                else:
                    on_explanation(self.explainer.explain(model, context=self._explainer_context))

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
                    if on_explanation is None:
                        yield self.explainer.explain(model, context=self._explainer_context)
                    else:
                        on_explanation(
                            self.explainer.explain(model, context=self._explainer_context)
                        )

    def _default_output(self):
        output = ""
        n = 0
        for answer in self.explain():
            n = 1
            output += f"Answer {n}\n"
            output += "\n".join([expl.ascii_tree() for expl in answer])
            output += "\n"
        return output
