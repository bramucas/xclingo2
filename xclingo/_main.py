from typing import Iterable
from clingo import Control as ClingoControl, backend
from clingo import Model, Function, String, Symbol
import clingo
from clingo.ast import Program, ProgramBuilder, parse_string, Location, Position
from clingo.control import Control
from xclingo.explanation import Explanation
from xclingo.preprocessor import Preprocessor
from time import time

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

def from_preorder_to_text(symbols:Iterable[Symbol]):
    parent_stack = None
    level_stack = None
    last_child = None
    expl_text = "  *\n"
    for i in range(len(symbols)-1, -1, -1):
        p, c, lab = symbols[i].arguments
        # initialises stack
        if parent_stack is None:
            parent_stack = [p]
            level_stack = [1]
        
        # check if the current parent is a child of the last element of the stack
        if p != parent_stack[-1]:
            if p in parent_stack:
                p_index = parent_stack.index(p)
                parent_stack = parent_stack[:p_index+1]
                level_stack = level_stack[:p_index+1]

            parent_stack.append(p)
            level_stack.append(level_stack[-1] + 1)
            expl_text+="\n"
        
        if c == last_child:
            expl_text += ";{label}".format(label=str(lab).strip('"'))
        else:
            expl_text+='{branch}{node}'.format(branch=ascii_branch(level_stack[-1]), node=str(lab).strip('"'))
            last_child = c

    return expl_text

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
        
        self._internal_control_arguments = internal_control_arguments
        self._translated = False
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

    def _retrieve1(self, control, yield_=True):
        with control.solve(yield_=yield_) as it:
            for expl_model in it:
                expl, labels = from_model(expl_model.symbols(shown=True))
                print(ascii_tree(expl, labels))

    def _retrieve2(self, control, yield_=True):
        total = 0
        with control.solve(yield_=yield_) as it:
            for expl_model in it:
                print(from_preorder_to_text(expl_model.symbols(shown=True)))

    def explain(self, model:Model, yield_=True) -> Iterable[Explanation]:
        control = Control(self._internal_control_arguments)
        
        t = time()
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
        # self._retrieve2(control, yield_=yield_)
