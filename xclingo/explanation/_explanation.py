from typing import Iterable, Mapping
from clingo import Symbol

class Explanation:

    @staticmethod
    def ascii_branch(level):
        if level > 0:
            return "  |" * (level) + "__"
        else:
            return ""

    @staticmethod
    def from_model(symbols:Iterable[Symbol]):
        roots = set()
        table = dict()
        labels = {'root': '*'}
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
    
    def preorder_iterator(self):
        stack = [iter([self])]
        level = 0
        while (stack):
            try:
                current = next(stack[-1])
                yield (current, level)
                stack.append(iter(current.causes))
                level += 1
            except StopIteration:
                stack.pop()
                level += -1

    def ascii_tree(self):
        expl = ""
        for node, level in self.preorder_iterator():
            expl += "{branch}{text}\n".format(
                branch=Explanation.ascii_branch(level),
                text=node.get_node_text(),
            )
        return expl

    def is_equal(self, other):
        if not isinstance(other, Explanation):
            return False

        for (node1, level1), (node2, level2) in zip(self.preorder_iterator(), other.preorder_iterator()):
            if not node1._node_equals(node2):
                return False

            if (level1 != level2):
                return False
        
        return True

class ExplanationRoot(Explanation):

    def __init__(self, causes=list()):
        if not isinstance(causes, list):
            raise RuntimeError("Parameter causes should be a list.")
        else:
            self.causes = causes

    def get_node_text(self):
        return "  *"

    def _node_equals(self, other):
        if not isinstance(other, ExplanationRoot):
            return False

        return True

class ExplanationNode(Explanation):
    """
    A non-binary tree.
    """

    def __init__(self, label, causes=list()):
        if isinstance(label, str):
            self.label = Label(label)
        elif not isinstance(label, Label):
            raise RuntimeError("Parameter label has to be a Label object.")
        else:
            self.label  = label

        if not isinstance(causes, list):
            raise RuntimeError("Parameter causes should be a list.")
        else:
            self.causes = causes

    def get_node_text(self):
        return self.label.replace_values()

    def _node_equals(self, other):
        if not isinstance(other, ExplanationNode):
            return False

        if self.label.replace_values() != other.label.replace_values():
            return False

        return True

class Label:

    def __init__(self, text, values=[], placeholder="%"):
        self.text = text
        self.values = values
        self.placeholder = placeholder

    def replace_values(self):
        processed_label = self.text
        for v in self.values:
            processed_label = processed_label.replace(self.placeholder, str(v), 1)
        return processed_label

    def __str__(self):
        return self.replace_values()