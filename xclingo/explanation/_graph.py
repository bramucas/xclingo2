from typing import Type, Iterable
from clingo import Symbol, Model
from collections import defaultdict


class ExplanationGraphModel(Model):
    def __init__(self, graph_model: Model):
        super().__init__(graph_model._rep)
        # Builds graph from model
        self.show_trace = []
        self.index = defaultdict()
        for s in self.symbols(shown=True):
            if len(s.arguments) == 1:  # _xclingo_show_trace(Atom)
                self.show_trace.append(s.arguments[0])
            elif len(s.arguments) == 2:  # _xclingo_edge((Caused, Cause), explanation)
                caused, cause = s.arguments[0].arguments
                self.index.setdefault(caused, Explanation(caused))
                self.index.setdefault(cause, Explanation(cause))
                self.index[caused].add_cause(self.index[cause])
            else:  # _xclingo_attr(node, Atom, label, Label)
                self.index.setdefault(s.arguments[1], Explanation(s.arguments[1]))
                self.index[s.arguments[1]].add_label(str(s.arguments[3]))

    def explain(self, symbol: Symbol):
        return self.index.get(symbol, None)


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
