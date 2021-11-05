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
    
    def __init__(self, internal_control_arguments=['1']):
        self._preprocessor = Preprocessor()
        self._memory = []
        
        self._internal_control_arguments = internal_control_arguments
        self._translated = False
        self._current_model = []

    def _getExplainerLP(self):
        if hasattr(self, '_explainerLP') == False:
            setattr(self, '_explainerLP', self._loadExplainerLP())
        return self._explainerLP

    def _loadExplainerLP(self):
        try:
            import importlib.resources as pkg_resources
        except ImportError:
            # Try backported to PY<37 `importlib_resources`.
            import importlib_resources as pkg_resources

        from . import xclingo_lp  # relative-import the *package* containing the templates
        return pkg_resources.read_text(xclingo_lp, 'xclingo.lp')

    def add(self, program_name:str, parameters: Iterable[str], program:str):
        self._memory.append(program)

    def _retrieve1(self, control, yield_=True):
        with control.solve(yield_=yield_) as it:
            for expl_model in it:
                expl = Explanation.from_model(expl_model.symbols(shown=True))
                print(expl.ascii_tree())


    def explain(self, model:Model, yield_=True) -> Iterable[Explanation]:
        control = Control(self._internal_control_arguments)
        
        if not self._translated:
            for program in self._memory:
                parse_string(
                    Preprocessor.translate_comments(program), 
                    lambda ast: self._preprocessor.translate_rule(ast),
                )
        with ProgramBuilder(control) as builder:
            parse_string(
                self._getExplainerLP()+self._preprocessor.get_translation(),
                lambda ast: builder.add(ast),
            )
        
        with control.backend() as backend:
            for sym in model.symbols(shown=True):
                atm_id = backend.add_atom(Function('_xclingo_model', [sym], True))
                backend.add_rule([atm_id], [], False)
            
        control.ground([('base', [])], context=Context())

        self._retrieve1(control, yield_=yield_)
