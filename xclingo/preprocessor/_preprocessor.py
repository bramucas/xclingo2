from typing import Callable, Iterable, Sequence
from clingo import ast
from clingo.symbol import Number
from ._utils import (
    is_xclingo_label,
    is_xclingo_show_trace,
    is_choice_rule,
    is_label_rule,
    is_xclingo_mute,
    is_constraint,
    is_disyunctive_head,
)


class Preprocessor:
    def __init__(self) -> None:
        self._translation = ""

    def reset(self) -> None:
        self._translation = ""

    def preprocess_rule(self, rule_ast: ast.AST) -> Sequence[ast.AST]:
        raise RuntimeError("This method is intended to be override")

    def _add_to_translation(self, rule_asts: Sequence[ast.AST]):
        """Adds the given rule to the internal translation.

        Args:
            rule_ast (ast.AST): the rule to add to the translation.
        """
        for ra in rule_asts:
            self._translation += f"{ra}\n"

    def _add_comment_to_translation(self, comment: str):
        """Adds a comment to the internal translation.

        Args:
            comment (str): the comment to add to the translation.
        """
        self._translation += f"% {comment}\n"

    def process_program(self, program: str):
        """Translates a given program into its xclingo translation. The translation starts with a comment containing the program name.

        Args:
            program (str): program to be translated.
            name (str, optional): Defaults to "".
        """
        self._translation = ""
        ast.parse_string(
            program,
            lambda ast: self._add_to_translation(self.preprocess_rule(ast)),
        )
        return self._translation


class XClingoAnnotationPreprocessor(Preprocessor):
    def __init__(self, func: Callable) -> None:
        super().__init__()
        self.func = func

    def reset(self) -> None:
        super().reset()

    def preprocess_rule(self, rule_ast: ast.AST) -> None:
        pass

    def process_program(self, program: str):
        self._translation = ""
        self._translation += self.func(program)
        return self._translation


class ConstraintRelaxer(Preprocessor):
    """Relaxes the constraints in the program. This is, traced constraints become rules with special
    heads.

    Created heads have the form: xclingo_violated_constraint(<number>). This number ID is
    independent from the number of rules in the program.
    """

    def __init__(self, preserve_labels=False):
        super().__init__()
        self._constraint_count = 1
        self._lits = []
        self.there_is_a_label = False
        self.preserve_labels = preserve_labels

    def reset(self):
        super().reset()
        self._constraint_count = 1
        self._lits = []
        self.there_is_a_label = False

    def _increment_constraint_count(self):
        """Returns the current ID for constraints and increment the internal counter."""
        n = self._constraint_count
        self._constraint_count += 1
        return n

    def preprocess_rule(self, rule_ast: ast.AST):
        """Preprocess the given rule and adds the result to the translation.

        Labelled constraints are transformed into their relaxed form. The rest of the program is
        unchanged.

        Args:
            rule_ast (ast.AST): rule to be preprocessed and added to the translation.
        """
        # if there is a label, self.there_is_a_label is set to True but it's not used
        if is_xclingo_label(rule_ast):
            self.there_is_a_label = True
            if self.preserve_labels:
                yield rule_ast
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
                                        loc,
                                        "",
                                        list(XClingoPreprocessor.propagates(rule_ast.body)),
                                        False,
                                    ),  # tuple
                                ],
                                False,
                            )
                        ),
                    ),
                    body=rule_ast.body,
                )
                rule_ast = new_rule
            self.there_is_a_label = False
            yield rule_ast


class XClingoPreprocessor(Preprocessor):
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
        super().__init__()
        self._rule_count = 1
        self._last_trace_rule = None

    def reset(self):
        super().reset()
        self._rule_count = 1
        self._last_trace_rule = None

    def _increment_rule_count(self):
        """Returns the current ID for rules and increment the internal counter."""
        n = self._rule_count
        self._rule_count += 1
        return n

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
                            loc, "", list(XClingoPreprocessor.propagates(rule_ast.body)), False
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
                            loc, "", list(XClingoPreprocessor.propagates(rule_ast.body)), False
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
                                list(XClingoPreprocessor.propagates(rule_body)),
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

    def preprocess_rule(self, rule_ast: ast.ASTType.Rule):
        """Translates a given rule into its xclingo translation and adds it to the translation.
        Before every addition, a comment containing the original rule is also added.

        Not traced constraints will be ignored.

        Args:
            rule_ast (ast.ASTType.Rule): rule to be translated.
        """
        self._add_comment_to_translation(rule_ast)
        if rule_ast.ast_type != ast.ASTType.Rule:
            yield rule_ast
        else:
            if is_xclingo_label(rule_ast):
                if is_label_rule(rule_ast):
                    self._last_trace_rule = rule_ast
                    return
                # if it is label atom
                yield self.label_atom(rule_ast)
            elif is_xclingo_show_trace(rule_ast):
                yield self.show_trace(rule_ast)
            elif is_xclingo_mute(rule_ast):
                yield self.mute(rule_ast)
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
                        yield self.support_rule(rule_id, false_rule)
                        yield self.fbody_rule(rule_id, false_rule)
                        if self._last_trace_rule is not None:
                            yield self.label_rule(rule_id, self._last_trace_rule, false_rule.body)
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
                                    loc,
                                    "",
                                    list(XClingoPreprocessor.propagates(rule_ast.body)),
                                    False,
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
                    yield self.support_rule(rule_id, false_rule)
                    yield self.fbody_rule(rule_id, false_rule)
                    yield self.label_rule(rule_id, self._last_trace_rule, false_rule.body)

                    self._last_trace_rule = None
                else:  # Other cases
                    yield self.support_rule(rule_id, rule_ast)
                    yield self.fbody_rule(rule_id, rule_ast)
                    if self._last_trace_rule is not None:
                        yield self.label_rule(rule_id, self._last_trace_rule, rule_ast.body)
                        self._last_trace_rule = None
