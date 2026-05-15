from clingo.ast import Transformer


class AnonVariableRenamer(Transformer):
    """
    Handles the renaming of anonymous '_' variables.
    """

    _anon_id = -1

    def visit_Variable(self, node):
        if node.name == "_":
            self._anon_id += 1
            return node.update(name=f"{node.name}XclingoAnon{str(self._anon_id)}")
        else:
            return node
