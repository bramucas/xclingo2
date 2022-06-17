from typing import Union, Sequence
from clingo import Model, Function, String, Symbol
from clingo.ast import ProgramBuilder, parse_string
from clingo.control import Control
from clingo.symbol import SymbolType
from pyrsistent import s
from xclingo.explanation import Explanation, ExplanationGraphModel
from xclingo.preprocessor import Preprocessor

from clingo.core import MessageCode


class Context:
    def label(self, text, tup):
        if text.type == SymbolType.String:
            text = text.string
        else:
            text = str(text).strip('"')
        for val in tup.arguments:
            text = text.replace("%", val.string if val.type == SymbolType.String else str(val), 1)
        return [String(text)]

    def inbody(self, body):
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
    def __init__(self, internal_control_arguments=["1"], auto_trace="none"):
        self._preprocessor = Preprocessor()
        self._memory = []

        self._internal_control_arguments = internal_control_arguments
        self._auto_trace = auto_trace
        self._translated = False
        self._current_model = []

        self._show_trace = []

        self._no_labels = False

    def logger(self, _code, msg):
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
        if self._no_labels:
            print("xclingo info: any atom or rule has been labelled.")
        if self._show_trace == []:
            print("xclingo info: any atom has been affected by a %!show_trace annotation.")

    ###############################
    def _getExplainerLP(self, auto_trace="none"):
        if hasattr(self, "_explainerLP") == False:
            setattr(self, "_explainerLP", self._loadExplainerLP(auto_trace))
        return self._explainerLP

    def _loadExplainerLP(self, auto_trace="none"):
        try:
            import importlib.resources as pkg_resources
        except ImportError:
            # Try backported to PY<37 `importlib_resources`.
            import importlib_resources as pkg_resources

        from . import xclingo_lp  # relative-import the *package* containing the templates

        program = pkg_resources.read_text(xclingo_lp, "xclingo.lp")
        if auto_trace == "all":
            program += pkg_resources.read_text(xclingo_lp, "autotrace_all.lp")
        elif auto_trace == "facts":
            program += pkg_resources.read_text(xclingo_lp, "autotrace_facts.lp")
        return program

    ################################
    def add(self, program_name: str, parameters: Sequence[str], program: str):
        self._memory.append((program_name, program))

    def _initialize_control(self):
        self._no_labels = False
        return Control(self._internal_control_arguments + ["--project=project"], logger=self.logger)

    def _translate_program(self):
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
                self._getExplainerLP(auto_trace=self._auto_trace)
                + self._preprocessor.get_translation(),
                lambda ast: builder.add(ast),
            )

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
    def __init__(self, n_solutions="1", n_explanations="1", auto_trace="none"):
        self.n_solutions = n_solutions
        self.n_explanations = n_explanations

        self.control = Control([n_solutions if type(n_solutions) == str else str(n_solutions)])
        self.explainer = Explainer(
            [
                n_explanations if type(n_explanations) == str else str(n_explanations),
            ],
            auto_trace=auto_trace,
        )

        self._explainer_context = None

    def add(self, name, parameters, program):
        """It adds a program to the control.

        Args:
            name (str): name of program block to add.
            parameters (Sequence[str]): a list (or Sequence) of for the program.
            program (str): a logic program in ASP format.
        """
        self.control.add("base", parameters, program)
        self.explainer.add(name, [], program)

    def ground(self, context=None):
        """Ground (only base for now) programs.

        Args:
            context (Object, optional): Context to be passed to the original program control. Defaults to None.
        """
        self.control.ground([("base", [])], context)

    def solve(self) -> Sequence[XClingoModel]:
        """Returns a generator of xclingo.explanation.Explanation objects. If on_explanation is not None, it is called for each explanation.

        Args:
            on_explanation (Callable, optional): callable that will be called for each Explanation, it must receive Explanation as a parameter. Defaults to None.

        Yields:
            Explation: a tree-like object that represents an explanation.
        """
        with self.control.solve(yield_=True) as it:
            for m in it:
                yield XClingoModel(m, self.explainer)

    def _default_output(self):
        output = ""
        nanswer = 0
        for answer in self.explain():
            nanswer += 1
            output += f"Answer: {nanswer}\n"
            nexpl = 0
            for explanation in answer.explain():
                nexpl += 1
                output += f"*Explanation: {nexpl}\n"
                output += "\n".join([expl.ascii_tree() for expl in answer])
                output += "\n"
            output += f"Total explanations: {nexpl}\n"
        output += f"Models: {nanswer}"
        return output
