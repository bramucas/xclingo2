from typing import Type
from typing import Iterable
from clingo import Symbol, Model
from collections import defaultdict


class ExplanationGraphModel(Model):
    def __init__(self, graph_model: Model):
        super().__init__(graph_model._rep)
        self._table = defaultdict()

        for s in self.symbols(shown=True):
            if s.name == "_xclingo_attr":  # _xclingo_attr(node, Atom, label, Label)
                self._table.setdefault(s.arguments[1], Explanation(s.arguments[1]))
                self._table[s.arguments[1]].add_label(str(s.arguments[3]))
            else:  # _xclingo_edge((Caused, Cause), explanation)
                caused, cause = s.arguments[0].arguments
                self._table.setdefault(caused, Explanation(caused))
                self._table.setdefault(cause, Explanation(cause))
                self._table[caused].add_cause(self._table[cause])

    def explain(self, symbol: Symbol):
        return self._table[symbol]


class Explanation:
    def __init__(self, atom: Symbol, labels: set = None, causes: set = None):
        self.labels = labels
        if self.labels is not None:
            if not isinstance(labels, set):
                raise TypeError('"labels" arguments must be of type set.')
        else:
            self.labels = set()

        self.causes = causes
        if self.causes is not None:
            if not isinstance(causes, list):
                raise TypeError('"child_nodes" arguments must be of type list.')
        else:
            self.causes = list()

        self.atom = atom

    def preorder_iterator(self):
        stack = [iter([self])]
        level = 1
        while stack:
            try:
                current = next(stack[-1])
                yield (current, level)
                stack.append(iter(current.causes))
                level += 1
            except StopIteration:
                stack.pop()
                level += -1

    def ascii_tree(self):
        def ascii_branch(level):
            if level > 0:
                return "  |" * (level) + "__"
            else:
                return ""

        expl = "  *\n"
        for node, level in self.preorder_iterator():
            expl += "{branch}{text}\n".format(
                branch=ascii_branch(level),
                text=node.get_node_text(),
            )
        return expl

    def get_node_text(self):
        return ";".join(sorted(list(self.labels)))

    def add_cause(self, cause):
        self.causes.append(cause)

    def add_label(self, label):
        self.labels.add(label)

    def __str__(self):
        return self.ascii_tree()
