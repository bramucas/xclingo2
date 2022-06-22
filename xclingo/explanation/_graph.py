from typing import Type, Iterable
from clingo import Symbol, Model
from collections import defaultdict


class ExplanationGraphModel(Model):
    def __init__(self, graph_model: Model):
        super().__init__(graph_model._rep)

    @property
    def show_trace(self):
        if not hasattr(self, "_index"):
            self.index
        return self._show_trace

    @property
    def index(self):
        if not hasattr(self, "_index"):
            # Builds graph from model
            setattr(self, "_show_trace", [])
            setattr(self, "_index", defaultdict())
            for s in self.symbols(shown=True):
                if len(s.arguments) == 1:  # _xclingo_show_trace(Atom)
                    self._show_trace.append(s.arguments[0])
                elif len(s.arguments) == 2:  # _xclingo_edge((Caused, Cause), explanation)
                    if s.name == "_xclingo_edge":
                        caused, cause = s.arguments[0].arguments
                    else:  # _xclingo_link(ToExplainAtom, Cause)
                        caused, cause = s.arguments
                    self._index.setdefault(caused, Explanation(caused))
                    self._index.setdefault(cause, Explanation(cause))
                    self._index[caused].add_cause(self._index[cause])
                else:  # _xclingo_attr(node, Atom, label, Label)
                    self._index.setdefault(s.arguments[1], Explanation(s.arguments[1]))
                    self._index[s.arguments[1]].add_label(str(s.arguments[3]))
        return self._index

    def explain(self, symbol: Symbol):
        return self._index.get(symbol, None)


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

    def preorder_iterator(self, only_labelled=False):
        if only_labelled and not self.labels:
            stack = [iter(self.causes)]
        else:
            stack = [iter([self])]
        level = 1
        while stack:
            try:
                current = next(stack[-1])
                yield (current, level)
                level += 1
                stack.append(iter(current.causes))
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
        for node, level in self.preorder_iterator(only_labelled=True):
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
