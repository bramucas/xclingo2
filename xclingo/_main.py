from typing import Iterable, Sequence
from clingo import Model, Function, String
from clingo.ast import ProgramBuilder, parse_string
from clingo.control import Control
from clingo.symbol import SymbolType
from xclingo.explanation import Explanation
from xclingo.preprocessor import Preprocessor

from clingo.core import MessageCode

class Context:
    def label(self, text, tup):
        if text.type == SymbolType.String:
            text = text.string
        else:
            text = str(text).strip('"')
        for val in tup.arguments:
            text = text.replace("%", val.string if val.type==SymbolType.String else str(val), 1)
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

        self._no_labels = False
        self._no_show_trace = False

    def logger(self, _code, msg):
        if _code == MessageCode.AtomUndefined:
            if 'xclingo_muted(Cause)' in msg:
                return
            if '_xclingo_label_tree/3' in msg:
                return
            if '_xclingo_label' in msg:
                self._no_labels = True
                return
            if '_xclingo_show_trace' in msg:
                self._no_show_trace = True
        print(msg)

    def print_messages(self):
        if self._no_labels:
            print('xclingo info: any atom or rule has been labelled.')
        if self._no_show_trace:
            print('xclingo info: any atom has been affected by a %!show_trace annotation.')
    
    def clean_log(self):
        self._no_labels = False
        self._no_show_trace = False

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
        self._memory.append((program_name, program))

    def _initialize_control(self):
        return Control(
            self._internal_control_arguments + \
                [
                    '--project=project'
                ], 
            logger=self.logger)

    def _translate_program(self):
        self._preprocessor._rule_count = 1
        for name, program in self._memory:
            self._preprocessor.translate_program(program, name=name)

    def _ground(self, control, model, context=None):
        if not self._translated:
            self._translate_program()
            self._translated
            
        with ProgramBuilder(control) as builder:
            parse_string(
                self._getExplainerLP(auto_trace=self._auto_trace)+self._preprocessor.get_translation(),
                lambda ast: builder.add(ast),
            )
        
        with control.backend() as backend:
            for sym in model.symbols(shown=True):
                atm_id = backend.add_atom(Function('_xclingo_model', [sym], True))
                backend.add_rule([atm_id], [], False)
            
        control.ground([('base', [])], context=context if context is not None else Context())


    def _get_explanations(self, control):
        with control.solve(yield_=True) as it:
            for expl_model in it:
                syms = expl_model.symbols(shown=True)
                if len(syms)>0:
                    yield Explanation.from_model(syms)
    
    def _get_models(self, control):
        with control.solve(yield_=True) as it:
            for expl_model in it:
                yield expl_model

    def get_xclingo_models(self, model:Model) -> Iterable[Explanation]:
        control = self._initialize_control()
        self.clean_log()
        self._ground(control, model)
        self.print_messages()
        return self._get_models(control)

    def explain(self, model:Model, context=None) -> Iterable[Explanation]:
        control = self._initialize_control()    
        self.clean_log()
        self._ground(control, model, context)
        self.print_messages()
        return self._get_explanations(control)


class XclingoControl:
    def __init__(self, n_solutions='1', n_explanations='1', auto_trace='none'):
        self.n_solutions = n_solutions
        self.n_explanations = n_explanations

        self.control = Control([n_solutions if type(n_solutions)==str else str(n_solutions)])
        self.explainer = Explainer(
            [
                n_explanations if type(n_explanations)==str else str(n_explanations), 
            ], 
            auto_trace=auto_trace
        )

        self._explainer_context = None

    def add(self, name, parameters, program):
        self.explainer.add(name, [], program)
        self.control.add("base", parameters, program)

    def ground(self, context=None, explainer_context=None):
        self.control.ground([("base", [])], context)

        self._explainer_context = explainer_context

    def explain(self, on_explanation=None):
        with self.control.solve(yield_=True) as it:
            for m in it:
                if on_explanation is None:
                    yield self.explainer.explain(m, context=self._explainer_context)
                else:
                    on_explanation(self.explainer.explain(m, context=self._explainer_context))

    def explain_and_print(self):
        print(self._default_output())

    def _default_output(self):
        output = ''
        n = 0
        for answer in self.explain():
            n = 1
            output += f'Answer {n}\n'
            output += '\n'.join([expl.ascii_tree() for expl in answer])
            output += '\n'
        return output