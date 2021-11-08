from typing import Iterable
from clingo import Symbol

class Explanation:

    @staticmethod
    def from_model(symbols:Iterable[Symbol]):
        table = dict()
        for s in symbols:
            parent = str(s.arguments[0])
            child = str(s.arguments[1])
            child_item = table.get(child, None)
            parent_item = table.get(parent, None)

            if child_item is None:
                child_item = ExplanationNode()
                table[child] = child_item
            child_item.add_label(str(s.arguments[2]).strip('"'))
            
            if parent_item is None:
                parent_item = ExplanationRoot(explanation_atoms=symbols) if parent == 'root' else ExplanationNode()
                parent_item.add_cause(child_item)
                table[parent] = parent_item
            
            if child_item not in parent_item.causes:
                parent_item.add_cause(child_item)
        
        return table['root']

    @staticmethod
    def ascii_branch(level):
        if level > 0:
            return "  |" * (level) + "__"
        else:
            return ""
    
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

    def add_cause(self, cause):
        self.causes.append(cause)

    def add_label(self, label):
        self.labels.append(label)

class ExplanationRoot(Explanation):

    def __init__(self, causes=None, explanation_atoms=None):
        self.causes = list() if causes is None else causes
        self._explanation_atoms = explanation_atoms

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

    def __init__(self, labels=None, causes=None):
        self.labels = list() if labels is None else labels
        self.causes = list() if causes is None else causes

    def get_node_text(self):
        return ";".join(self.labels)

    def _node_equals(self, other):
        if not isinstance(other, ExplanationNode):
            return False

        if self.label.replace_values() != other.label.replace_values():
            return False

        return True
