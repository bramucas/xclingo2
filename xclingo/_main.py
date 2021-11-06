from typing import Iterable
from clingo import Model, Function, String
from clingo.ast import ProgramBuilder, parse_string
from clingo.control import Control
from xclingo.explanation import Explanation
from xclingo.preprocessor import Preprocessor

class Context:
    def label(self, text, tup):
        text = str(text).strip('"')
        for val in tup.arguments:
            text = text.replace("%", str(val), 1)
        return [String(text)]

    def inbody(self, body):
        if len(body.arguments)>0:
            return [Function(
                '',
                [a, body],
                True,
            )
            for a in body.arguments]
        else:
            return Function('empty', [], True)

class Explainer():
    
    def __init__(self, internal_control_arguments=['1'], auto_trace="none"):
        self._preprocessor = Preprocessor()
        self._memory = []
        
        self._internal_control_arguments = internal_control_arguments 
        self._auto_trace = auto_trace
        self._translated = False
        self._current_model = []

    def _getExplainerLP(self, auto_trace="none"):
        if hasattr(self, '_explainerLP') == False:
            setattr(self, '_explainerLP', self._loadExplainerLP(auto_trace))
        return self._explainerLP

    def _loadExplainerLP(self, auto_trace="none"):
        try:
            import importlib.resources as pkg_resources
        except ImportError:
            # Try backported to PY<37 `importlib_resources`.
            import importlib_resources as pkg_resources

        from . import xclingo_lp  # relative-import the *package* containing the templates
        program = pkg_resources.read_text(xclingo_lp, 'xclingo.lp')
        if auto_trace == "all":
            program += pkg_resources.read_text(xclingo_lp, 'autotrace_all.lp')
        elif auto_trace == "facts":
            program += pkg_resources.read_text(xclingo_lp, 'autotrace_facts.lp')
        return program

    def add(self, program_name:str, parameters: Iterable[str], program:str):
        self._memory.append(program)

    def initialize_control(self):
        return Control(self._internal_control_arguments)

    def _translate_program(self):
        for program in self._memory:
                parse_string(
                    Preprocessor.translate_comments(program), 
                    lambda ast: self._preprocessor.translate_rule(ast),
                )

    def _ground(self, control, model):
        if not self._translated:
            self._translate_program()
            
        with ProgramBuilder(control) as builder:
            parse_string(
                self._getExplainerLP(auto_trace=self._auto_trace)+self._preprocessor.get_translation(),
                lambda ast: builder.add(ast),
            )
        
        with control.backend() as backend:
            for sym in model.symbols(shown=True):
                atm_id = backend.add_atom(Function('_xclingo_model', [sym], True))
                backend.add_rule([atm_id], [], False)
            
        control.ground([('base', [])], context=Context())

    def _get_explanations(self, control):
        with control.solve(yield_=True) as it:
            for expl_model in it:
                yield Explanation.from_model(expl_model.symbols(shown=True))
    
    def _get_models(self, control):
        with control.solve(yield_=True) as it:
            for expl_model in it:
                yield expl_model

    def get_xclingo_models(self, model:Model) -> Iterable[Explanation]:
        control = Control(self._internal_control_arguments)        
        self._ground(control, model)
        return self._get_models(control)

    def explain(self, model:Model) -> Iterable[Explanation]:
        control = Control(self._internal_control_arguments)        
        self._ground(control, model)
        return self._get_explanations(control)
