from typing import Iterable
from clingo import Control as ClingoControl
from clingo import Model, Function, String, Symbol
import clingo
from clingo.ast import Program, ProgramBuilder, parse_string
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

def from_model(symbols:Iterable[Symbol]):
        roots = set()
        table = dict()
        labels = {"root": ["  *"]}
        for s in symbols:
            parent = str(s.arguments[0])
            child = str(s.arguments[1])

            if child in labels:
                labels[child].append(str(s.arguments[2]).strip('"'))
            else:
                labels[child] = [str(s.arguments[2]).strip('"')]

            child_item = table.get(child, None)
            if child_item is None:
                child_item = {}
                table[child] = child_item
            else:
                roots.discard(child)
            
            parent_item = table.get(parent, None)
            if parent_item is None:
                table[parent] = {child: child_item}
                roots.add(parent)
            else:
                parent_item[child] = child_item

        return {node : table[node] for node in roots}, labels


def preorder_iterator(d:dict, labels:dict):
    stack = [iter(d.items())]
    level = 0
    while (stack):
        try:
            k, v = next(stack[-1])
            yield (";".join(labels[k]), level)
            stack.append(iter(v.items()))
            level += 1
        except StopIteration:
            stack.pop()
            level += -1

def ascii_branch(level):
        if level > 0:
            return "  |" * (level) + "__"
        else:
            return ""

def ascii_tree(expl_dict, labels):
        expl = ""
        for node, level in preorder_iterator(expl_dict, labels):
            expl += f'{ascii_branch(level)}{node}\n'
        return expl

class Explainer():
    
    def __init__(self, internal_control_arguments=['1']):
        self._preprocessor = Preprocessor()
        self._memory = []
        

        self._control = ClingoControl(internal_control_arguments)
        self._grounded = False
        self._current_model = []

    def _clean_model_atoms(self):
        for a_id in self._current_model:
            self._control.assign_external(a_id, False)

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

    def explain(self, model:Model, yield_=True) -> Iterable[Explanation]:
        control = self._control
        
        if not self._grounded:
            with ProgramBuilder(control) as builder:
                for program in self._memory:
                    parse_string(
                        Preprocessor.translate_comments(program), 
                        lambda ast: self._preprocessor.translate(ast, builder),
                    )
                parse_string(
                    self._getExplainerLP(),
                    lambda ast: builder.add(ast),
                )
            self._grounded = True

        
        self._current_model = model.symbols(atoms=True)
        with control.backend() as backend:
            for sym in self._current_model:
                model_atm_id = backend.add_atom(Function('_xclingo_model', [sym], True))
                backend.add_external(model_atm_id, clingo.TruthValue.True_)
                # asumo que: si el atomo ya está no lo añade dos veces
        control.ground([("base", [])], context=Context())

        from time import time
        total_t = 0
        
        with control.solve(yield_=yield_) as it:
            for expl_model in it:
                t = time()
                expl, labels = from_model(expl_model.symbols(shown=True))
                print(ascii_tree(expl, labels))
                total_t+=time()-t
        
        print(f'tiempo invertido en recuperar explicaciones: {total_t}')
