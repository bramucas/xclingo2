from clingo import ast

class XClingoAST():
    _internal_ast = None  # Type: ast.AST
    type = None  # Type: ast.AST.ASTType
    child_keys = None  # Type: List [ str ]

    # l =[method for method in dir(my_ast) if method != 'use_enumeration_assumption' and callable(getattr(my_ast, method))]

    def __init__(self, base_ast):
        """

        @param ast.AST base_ast:
        """
        self.type = base_ast.ast_type
        self.child_keys = base_ast.child_keys
        self._internal_ast = base_ast  # must be at the end      

    """ast.AST methods"""
    def items(self):
        return self._internal_ast.items()

    def keys(self):
        return self._internal_ast.keys()

    def values(self):
        return self._internal_ast.values()

    """container methods and other"""
    def __contains__(self, item):
        return self._internal_ast.__contains__(item)

    def __getitem__(self, item):
        item = self._internal_ast.__getattr__(item)
        if type(item) == ast.AST:
            return XClingoAST(item)
        if type(item) == ast.ASTSequence:
            new_list = []
            for i in item:
                if type(i) == ast.AST:
                    new_list.append(XClingoAST(i))
                else:
                    new_list.append(i)
            return new_list
        else:
            return item

    def __delattr__(self, item):
        self._internal_ast.__delattr__(item)

    def __delitem__(self, key):
        self._internal_ast.__delitem__(key)

    def __eq__(self, other):
        return self._internal_ast.__eq__(other)

    def __format__(self, format_spec):
        return self._internal_ast.__format__(format_spec)

    def __ge__(self, other):
        return self._internal_ast.__ge__(other)

    # def __getattr__(self, item):
    #     return self._internal_ast.__getattr__(item)

    def __gt__(self, other):
        return self._internal_ast.__gt__(other)

    def __iter__(self):
        return self._internal_ast.__iter__()

    def __le__(self, other):
        return self._internal_ast.__le__()

    def __len__(self):
        return self._internal_ast.__len__()

    def __lt__(self, other):
        return self._internal_ast.__lt__()

    def __ne__(self, other):
        return self._internal_ast.__ne__()

    # def __setattr__(self, key, value):
    #     self._internal_ast.__setattr__(key, value)

    def __setitem__(self, key, value):
        self._internal_ast.__setattr__(key, value)

    def __str__(self):
        return self._internal_ast.__str__()

    """XclingoAST methods"""

    def is_constraint(self):
        """
        @return bool: True if the rule is a constraint, False if not.
        """
        return self['head']['atom'].type == ast.ASTType.BooleanConstant and self['head']['atom']['value'] == False

    def is_trace_all_rule(self):
        """
        @return bool: True if the rule is an instance of a xclingo trace_all rule, False if not.
        """
        return self['head'].type == ast.ASTType.TheoryAtom and self['head']['term']['name'] == "trace_all"

    def is_show_all_rule(self):
        """
        @return bool: True if the rule is an instance of a xclingo show_all rule, False if not.
        """
        return str(self['head']).startswith("show_all_") or str(self['head']).startswith("nshow_all_")

    def add_prefix(self, prefix):
        """
        It will try to add a prefix to this AST. It can raise an exception if the action has no sense (this depends on
        the type of the AST). If the ast is Rule type, then the prefix will be added only to the atoms in the body if it
        has a body, or only to the atom in the head in the other case.

        @param str prefix: the prefix that is intended to be added to the AST.
        @return None:
        """
        # Rules special case
        if self.type == ast.ASTType.Rule:
            # Rules with body
            if self['body']:
                # Adds the prefix to all the asts in the body but not to the head
                for b_ast in self['body']:
                    b_ast.add_prefix(prefix)
                return
            # Facts (rules without body)
            else:
                # Adds the prefix to the ast of the head
                self['head'].add_prefix(prefix)
        else:
            fun = self.get_function()
            if fun is not None:
                fun['name'] = prefix + fun['name']

    def get_function(self):
        """
        If the AST has a unique function inside of it (some types as Comparison can have multiple functions) then it
        will return it.
        @return XClingoAST: the function inside of the ast.
        """
        if self.type in (ast.ASTType.Function, ast.ASTType.TheoryFunction):
            return self

        if self.type == ast.ASTType.SymbolicAtom:
            return self['symbol'].get_function()

        if self.type == ast.ASTType.UnaryOperation:
            return self['argument'].get_function()

        if self.type == ast.ASTType.Literal:
            return self['atom'].get_function()

        if self.type in (ast.ASTType.Comparison, ast.ASTType.BooleanConstant):
            return None

        print(self)
        print(self.type)
        raise RuntimeError(str(self.type) + "  do not have Function.")
