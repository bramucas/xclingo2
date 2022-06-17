from typing import Iterable
from clingo import ast
from clingo.symbol import Number
from ._utils import (
    translate_show_all,
    translate_trace,
    translate_trace_all,
    translate_mute,
    is_xclingo_label,
    is_xclingo_show_trace,
    is_choice_rule,
    is_label_rule,
    is_xclingo_mute,
    is_constraint,
    is_disyunctive_head,
)


class ConstraintRelaxer:
    """Relaxes the constraints in the program. This is, traced constraints become rules with special
    heads.

    Created heads have the form: xclingo_violated_constraint(<number>). This number ID is
    independent from the number of rules in the program.
    """

    def __init__(self):
        self._constraint_count = 1
        self._lits = []
        self.there_is_a_label = False
        self._translation = ""

    def _increment_constraint_count(self):
        """Returns the current ID for constraints and increment the internal counter."""
        n = self._constraint_count
        self._constraint_count += 1
        return n

    def _add_to_translation(self, rule_ast: ast.AST):
        """Adds the given rule to the internal translation.

        Args:
            rule_ast (ast.AST): the rule to add to the translation.
        """
        self._translation += f"{rule_ast}\n"

    def _add_comment_to_translation(self, comment: str):
        """Adds a comment to the internal translation.

        Args:
            comment (str): the comment to add to the translation.
        """
        self._translation += f"% {comment}\n"

    def relax_labelled_constraint(self, rule_ast: ast.AST):
        """Preprocess the given rule and adds the result to the translation.

        Labelled constraints are transformed into their relaxed form. The rest of the program is
        unchanged.

        Args:
            rule_ast (ast.AST): rule to be preprocessed and added to the translation.
        """
        # if there is a label, self.there_is_a_label is set to True but it's not used
        if is_xclingo_label(rule_ast):
            self.there_is_a_label = True
        else:
            if rule_ast.ast_type == ast.ASTType.Rule:
                rule_id = self._increment_constraint_count()
            #  if there is a constraint and self.there_is_a_label is True, we put a head and add it to the translation
            if is_constraint(rule_ast) and self.there_is_a_label is True:
                loc = ast.Location(
                    ast.Position("", 0, 0),
                    ast.Position("", 0, 0),
                )
                new_rule = ast.Rule(
                    location=loc,
                    head=ast.Literal(
                        location=loc,
                        sign=ast.Sign.NoSign,
                        atom=ast.SymbolicAtom(
                            ast.Function(
                                loc,
                                f"_xclingo_violated_constraint",
                                [
                                    ast.SymbolicTerm(loc, Number(rule_id)),
                                    ast.Function(
                                        loc, "", list(Preprocessor.propagates(rule_ast.body)), False
                                    ),  # tuple
                                ],
                                False,
                            )
                        ),
                    ),
                    body=rule_ast.body,
                )
                rule_ast = new_rule
            self._add_to_translation(rule_ast)
            self.there_is_a_label = False

    def preprocess(self, program: str):
        """Preprocess the given program and stores the result in the internal translation.

        Args:
            program (str): the program to be preprocessed.
        """
        ast.parse_string(
            translate_trace(program),
            lambda ast: self.relax_labelled_constraint(ast),
        )

    def get_translation(self):
        """Returns the internal translation."""
        return self._translation


class Preprocessor:
    """Translates a given program into the xclingo format.

    For every original rule ID is given and the following happens:
    - the original rule is added as a comment in the translation.
    - a support rule (_xclingo_sup/3) is added to the translation. The body of this rule is the positive
    part of the original rule, written in terms of _xclngo_model/1 facts.
    - a fired_body rule (_xclingo_fbody/3) is added to the translation. The body of this rule is the
    positive part of the orignal rule, written in terms of _xclingo_f_atom/1 facts.
    - if the rule is traced, a label rule (_xclingo_label/2) is added to the translation. The body of
    this rule directly depends of the corresponding _xclingo_f/3 fact of the traced rule.
    - traced constraints are also translated into their xclingo forms. Not traced constraints are
    ignored.

    xClingo anotations are translated into its xclingo forms:
    - %!show_trace: translated into a rule with head _xclingo_show_trace/1.
    - %!trace: translated into a rule with head _xclingo_trace/2.
    """

    def __init__(self):
        self._rule_count = 1
        self._last_trace_rule = None
        self._translation = ""

    def _increment_rule_count(self):
        """Returns the current ID for rules and increment the internal counter."""
        n = self._rule_count
        self._rule_count += 1
        return n

    @staticmethod
    def _translate_annotations(program):
        """Translates the xclingo annotations in the program into a preliminary form of xclingo rules."""
        return translate_trace_all(translate_show_all(translate_trace(translate_mute(program))))

    @staticmethod
    def propagates(lit_list: Iterable[ast.AST]):
        """Captures the part of a body that propagate causes.
        This is, the positive part of the body of a rule. Comparison literals are ignored.

        Args:
            lit_list (Iterable[ast.AST]): list of literals to be processed. Normally
            a rule's body.

        Yields:
            ast.AST: literals that propagate cause.
        """
        for lit in lit_list:
            if lit.sign == ast.Sign.NoSign and lit.atom.ast_type == ast.ASTType.SymbolicAtom:
                yield lit

    def _sup_body(self, lit_list: Iterable[ast.AST]):
        """Returns the body of the support rule, given the body of an original rule.

        Args:
            lit_list (Iterable[ast.AST]): list of literals to be processed. Normally
            a rule's body.

        Yields:
            ast.AST: literals for the support rule.
        """
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        for lit in lit_list:
            if lit.ast_type == ast.ASTType.Literal:
                if lit.atom.ast_type == ast.ASTType.SymbolicAtom:
                    yield ast.Literal(
                        loc,
                        lit.sign,
                        ast.SymbolicAtom(
                            ast.Function(
                                loc,
                                "_xclingo_model",
                                [lit.atom.symbol],
                                False,
                            )
                        ),
                    )

                elif lit.atom.ast_type == ast.ASTType.BodyAggregate:
                    yield ast.Literal(
                        loc,
                        lit.sign,
                        ast.BodyAggregate(
                            loc,
                            left_guard=lit.atom.left_guard,
                            function=lit.atom.function,
                            elements=[
                                ast.BodyAggregateElement(
                                    terms=list(self._sup_body(e.terms)),
                                    condition=list(self._sup_body(e.condition)),
                                )
                                for e in lit.atom.elements
                            ],
                            right_guard=lit.atom.right_guard,
                        ),
                    )

                else:
                    yield lit

            else:
                yield lit

    def _sup_head(self, rule_id: int, rule_ast: ast.ASTType.Rule):
        """Returns the head of the support rule, given the original rule.

        Args:
            rule_id (int): xclingo ID for the rule.
            rule_ast (ast.ASTType.Rule): orinial rule.

        Returns:
            ast.AST: head of the support rule.
        """
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(
                ast.Function(
                    loc,
                    "_xclingo_sup",
                    [
                        ast.SymbolicTerm(loc, Number(rule_id)),
                        rule_ast.head.atom,
                        ast.Function(
                            loc, "", list(Preprocessor.propagates(rule_ast.body)), False
                        ),  # tuple
                    ],
                    False,
                ),
            ),
        )
        return head

    def support_rule(self, rule_id: int, rule_ast: ast.ASTType.Rule):
        """Returns the support rule, given the original rule.

        Args:
            rule_id (int): xclingo ID for the rule.
            rule_ast (ast.ASTType.Rule): original rule.

        Returns:
            ast.ASTType.Rule: the corresponding support rule.
        """
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        head = self._sup_head(rule_id, rule_ast)
        body = list(self._sup_body(rule_ast.body))

        return ast.Rule(loc, head, body)

    def _fbody_head(self, rule_id: int, rule_ast: ast.ASTType.Rule):
        """Returns the head of the fbody rule, given the original rule.

        Args:
            rule_id (int): xclingo ID for the rule.
            rule_ast (ast.ASTType.Rule): orinial rule.

        Returns:
            ast.AST: the head of the fbody rule.
        """ """"""
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(
                ast.Function(
                    loc,
                    "_xclingo_fbody",
                    [
                        ast.SymbolicTerm(loc, Number(rule_id)),
                        rule_ast.head.atom,
                        ast.Function(
                            loc, "", list(Preprocessor.propagates(rule_ast.body)), False
                        ),  # tuple
                    ],
                    False,
                ),
            ),
        )
        return head

    def _fbody_body(self, lit_list: Iterable[ast.AST]):
        """Returns the body of the fbody rule, given the body of an original rule.

        Args:
            lit_list (Iterable[ast.AST]): list of literals to be processed. Normally
            a rule's body.

        Yields:
            ast.AST: literals for the fbody rule.
        """
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        for lit in lit_list:
            if lit.ast_type == ast.ASTType.Literal:
                if lit.atom.ast_type == ast.ASTType.SymbolicAtom:
                    if lit.sign == ast.Sign.NoSign:
                        yield ast.Literal(
                            loc,
                            lit.sign,
                            ast.SymbolicAtom(
                                ast.Function(
                                    loc,
                                    "_xclingo_f_atom",
                                    [lit.atom.symbol],
                                    False,
                                )
                            ),
                        )
                    else:
                        yield ast.Literal(
                            loc,
                            ast.Sign.Negation,
                            ast.SymbolicAtom(
                                ast.Function(
                                    loc,
                                    "_xclingo_model",
                                    [lit.atom.symbol],
                                    False,
                                )
                            ),
                        )

                elif lit.atom.ast_type == ast.ASTType.BodyAggregate:
                    yield ast.Literal(
                        loc,
                        lit.sign,
                        ast.BodyAggregate(
                            loc,
                            left_guard=lit.atom.left_guard,
                            function=lit.atom.function,
                            elements=[
                                ast.BodyAggregateElement(
                                    terms=list(self._fbody_body(e.terms)),
                                    condition=list(self._fbody_body(e.condition)),
                                )
                                for e in lit.atom.elements
                            ],
                            right_guard=lit.atom.right_guard,
                        ),
                    )

                else:
                    yield lit
            else:
                yield lit

    def fbody_rule(self, rule_id: int, rule_ast: ast.ASTType.Rule):
        """Returns the fbody rule, given the original rule.

        Args:
            rule_id (int): xclingo ID for the rule.
            rule_ast (ast.ASTType.Rule): original rule.

        Returns:
            ast.ASTType.Rule: the corresponding fbody rule.
        """
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        head = self._fbody_head(rule_id, rule_ast)
        body = list(self._fbody_body(rule_ast.body))
        return ast.Rule(loc, head, body)

    def label_rule(
        self,
        rule_id: int,
        label_rule_ast: ast.ASTType.Rule,
        rule_body: Iterable[ast.AST],
    ):
        """Returns the final label rule, given the preliminary label rule (label_rule_ast) and the body of the original rule.

        Args:
            rule_id (int): xclingo ID for the rule that will be labelled.
            label_rule_ast (ast.ASTType.Rule): ast for the preliminary label rule.
            rule_body (Iterable[ast.AST]): body of the original rule (that is been labelled).

        Returns:
            ast.ASTType.Rule: final label rule.
        """ """"""
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        head_var = ast.Variable(loc, "Head")
        head = ast.Literal(
            loc,
            label_rule_ast.head.sign,
            ast.SymbolicAtom(
                ast.Function(
                    loc,
                    label_rule_ast.head.atom.symbol.name,
                    [head_var, label_rule_ast.head.atom.symbol.arguments[1]],
                    False,
                )
            ),
        )
        body = [
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        "_xclingo_f",
                        [
                            ast.SymbolicTerm(loc, Number(rule_id)),
                            head_var,
                            ast.Function(
                                loc,
                                "",
                                list(Preprocessor.propagates(rule_body)),
                                False,
                            ),
                        ],
                        False,
                    )
                ),
            )
        ]
        rule = ast.Rule(loc, head, body)
        return rule

    def label_atom(self, rule_ast: ast.ASTType.Rule):
        """Translates the preliminary form of a label atom rule into its final form.

        Args:
            rule_ast (ast.ASTType.Rule): preliminary label atom rule.

        Returns:
            ast.ASTType.Rule: translated label atom rule.
        """ """"""
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        fatom = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(
                ast.Function(
                    loc,
                    "_xclingo_f_atom",
                    [rule_ast.head.atom.symbol.arguments[0]],
                    False,
                )
            ),
        )
        body = [fatom] + list(self._sup_body(rule_ast.body))
        rule = ast.Rule(loc, rule_ast.head, body)
        return rule

    def show_trace(self, rule_ast: ast.ASTType.Rule):
        """Translates the preliminary form of a show trace rule into its final form.

        Args:
            rule_ast (ast.ASTType.Rule): preliminary show trace rule.

        Returns:
            ast.ASTType.rule: translated show trace rule.
        """
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        literal_head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(rule_ast.head.atom.symbol.arguments[0]),
        )
        rule = ast.Rule(
            loc, rule_ast.head, list(self._sup_body([literal_head] + list(rule_ast.body)))
        )
        return rule

    def mute(self, rule_ast: ast.ASTType.Rule):
        """Translates the preliminary form of a mute rule into its final form.

        Args:
            rule_ast (ast.ASTType.Rule): preliminary mute rule.

        Returns:
            ast.ASTType.Rule: translated mute rule.
        """ """"""
        loc = ast.Location(
            ast.Position("", 0, 0),
            ast.Position("", 0, 0),
        )
        literal_head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(rule_ast.head.atom.symbol.arguments[0]),
        )
        rule = ast.Rule(
            loc, rule_ast.head, list(self._sup_body([literal_head] + list(rule_ast.body)))
        )
        return rule

    def add_to_translation(self, some_ast: ast.AST):
        """Adds an AST to the translation.

        Args:
            ast (ast.AST): an AST to be added.
        """
        self._translation += f"{some_ast}\n"

    def add_comment_to_translation(self, comment: object):
        """Adds a comment to the translation.

        Args:
            comment (object): a comment to be added.
        """
        self._translation += f"% {comment}\n"

    def translate_rule(self, rule_ast: ast.ASTType.Rule):
        """Translates a given rule into its xclingo translation and adds it to the translation.
        Before every addition, a comment containing the original rule is also added.

        Not traced constraints will be ignored.

        Args:
            rule_ast (ast.ASTType.Rule): rule to be translated.
        """
        self.add_comment_to_translation(rule_ast)
        if rule_ast.ast_type == ast.ASTType.Rule:
            if is_xclingo_label(rule_ast):
                if is_label_rule(rule_ast):
                    self._last_trace_rule = rule_ast
                    return
                # if it is label atom
                self.add_to_translation(self.label_atom(rule_ast))
            elif is_xclingo_show_trace(rule_ast):
                self.add_to_translation(self.show_trace(rule_ast))
            elif is_xclingo_mute(rule_ast):
                self.add_to_translation(self.mute(rule_ast))
            else:
                rule_id = self._increment_rule_count()

                if is_choice_rule(rule_ast) or is_disyunctive_head(rule_ast):
                    for cond_lit in rule_ast.head.elements:
                        false_rule = ast.Rule(
                            ast.Location(
                                ast.Position("", 0, 0),
                                ast.Position("", 0, 0),
                            ),
                            cond_lit.literal,
                            list(cond_lit.condition) + list(rule_ast.body),
                        )
                        self.add_to_translation(self.support_rule(rule_id, false_rule))
                        self.add_to_translation(self.fbody_rule(rule_id, false_rule))
                        if self._last_trace_rule is not None:
                            self.add_to_translation(
                                self.label_rule(rule_id, self._last_trace_rule, false_rule.body)
                            )
                    if self._last_trace_rule is not None:
                        self._last_trace_rule = None
                elif is_constraint(rule_ast) and self._last_trace_rule is not None:
                    loc = ast.Location(ast.Position("", 0, 0), ast.Position("", 0, 0))
                    head_sym = ast.SymbolicAtom(
                        ast.Function(
                            loc,
                            "_xclingo_violated_constraint",
                            [
                                ast.SymbolicTerm(loc, Number(rule_id)),
                                ast.Function(
                                    loc, "", list(Preprocessor.propagates(rule_ast.body)), False
                                ),  # tuple
                            ],
                            False,
                        ),
                    )
                    false_head = ast.Literal(
                        loc,
                        ast.Sign.NoSign,
                        head_sym,
                    )
                    false_rule = ast.Rule(
                        loc,
                        false_head,
                        rule_ast.body,
                    )
                    self.add_to_translation(self.support_rule(rule_id, false_rule))
                    self.add_to_translation(self.fbody_rule(rule_id, false_rule))
                    self.add_to_translation(
                        self.label_rule(rule_id, self._last_trace_rule, false_rule.body)
                    )
                    self._last_trace_rule = None
                else:  # Other cases
                    self.add_to_translation(self.support_rule(rule_id, rule_ast))
                    self.add_to_translation(self.fbody_rule(rule_id, rule_ast))
                    if self._last_trace_rule is not None:
                        self.add_to_translation(
                            self.label_rule(rule_id, self._last_trace_rule, rule_ast.body)
                        )
                        self._last_trace_rule = None

    def translate_program(self, program: str, name: str = ""):
        """Translates a given program into its xclingo translation. The translation starts with a comment containing the program name.

        Args:
            program (str): program to be translated.
            name (str, optional): Defaults to "".
        """
        self._translation += "%" * 8 + name + "%" * 8 + "\n"
        ast.parse_string(
            Preprocessor._translate_annotations(program),
            lambda ast: self.translate_rule(ast),
        )

    def get_translation(self):
        """Returns the translation so far."""
        return self._translation
