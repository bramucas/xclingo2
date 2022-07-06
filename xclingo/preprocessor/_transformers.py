from ast import AST
from re import S
from attr import has
from clingo import Function, ast, Number
from typing import Sequence

# TODO: fix location
loc = ast.Location(
    ast.Position("", 0, 0),
    ast.Position("", 0, 0),
)


def propagates(lit_list: Sequence[ast.AST]):
    """Captures the part of a body that propagate causes.
    This is, the positive part of the body of a rule. Comparison literals are ignored.

    Args:
        lit_list (Sequence[ast.AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        ast.AST: literals that propagate cause.
    """
    for lit in lit_list:
        if (
            lit.ast_type != ast.ASTType.ConditionalLiteral
            and lit.sign == ast.Sign.NoSign
            and lit.atom.ast_type == ast.ASTType.SymbolicAtom
        ):
            yield lit


def aggregates(lit_list: Sequence[ast.AST]):
    """Captures the part of a body that is an aggregate.

    Args:
        lit_list (Sequence[ast.AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        ast.AST: literals that are aggregates.
    """
    for lit in lit_list:
        if (
            lit.ast_type != ast.ASTType.ConditionalLiteral
            and lit.sign == ast.Sign.NoSign
            and lit.atom.ast_type == ast.ASTType.BodyAggregate
        ):
            for e in lit.atom.elements:
                yield e


def conditional_literals(lit_list: Sequence[ast.AST]):
    """Captures the part of a body that is a conditional literal.

    Args:
        lit_list (Sequence[ast.AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        ast.AST: literals that are conditional literals.
    """
    for lit in lit_list:
        if lit.ast_type == ast.ASTType.ConditionalLiteral:
            yield lit


def collect_free_vars(lit_list: Sequence[ast.AST]):
    seen_vars = set()
    for lit in lit_list:
        # handle conditional literals
        if lit.ast_type == ast.ASTType.ConditionalLiteral:
            continue

        # handle comparisons
        elif lit.atom.ast_type == ast.ASTType.Comparison:
            if lit.atom.left.ast_type == ast.ASTType.Variable:
                seen_vars.add(str(lit.atom.left.name))
            if lit.atom.right.ast_type == ast.ASTType.Variable:
                seen_vars.add(str(lit.atom.right.name))

        # Skip negative literals
        elif lit.sign != ast.Sign.NoSign:
            continue

        # handle positive body literals
        elif lit.atom.ast_type == ast.ASTType.SymbolicAtom:
            for arg in lit.atom.symbol.arguments:
                if arg.ast_type == ast.ASTType.Variable:
                    seen_vars.add(str(arg.name))
            continue

    for var_name in seen_vars:
        yield ast.Variable(loc, var_name)


def _sup_body(lit_list: Sequence[ast.AST]):
    """Returns the body of the support rule, given the body of an original rule.

    Args:
        lit_list (Sequence[ast.AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        ast.AST: literals for the support rule.
    """
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
                                terms=list(_sup_body(e.terms)),
                                condition=list(_sup_body(e.condition)),
                            )
                            for e in lit.atom.elements
                        ],
                        right_guard=lit.atom.right_guard,
                    ),
                )

            else:
                yield lit

        elif lit.ast_type == ast.ASTType.ConditionalLiteral:
            yield ast.ConditionalLiteral(
                loc,
                literal=ast.Literal(
                    loc,
                    lit.literal.sign,
                    ast.SymbolicAtom(
                        ast.Function(
                            loc,
                            "_xclingo_model",
                            [lit.literal.atom.symbol],
                            False,
                        )
                    ),
                ),
                condition=list(_sup_body(lit.condition)),
            )

        else:
            yield lit


def _sup_head(rule_id: int, disjunction_id: int, rule_ast: ast.ASTType.Rule):
    """Returns the head of the support rule, given the original rule.

    Args:
        rule_id (int): xclingo ID for the rule.
        rule_ast (ast.ASTType.Rule): orinial rule.

    Returns:
        ast.AST: head of the support rule.
    """
    head = ast.Literal(
        loc,
        ast.Sign.NoSign,
        ast.SymbolicAtom(
            ast.Function(
                loc,
                "_xclingo_sup",
                [
                    ast.SymbolicTerm(loc, Number(rule_id)),
                    ast.SymbolicTerm(loc, Number(disjunction_id)),
                    rule_ast.head.atom,
                    ast.Function(loc, "", list(collect_free_vars(rule_ast.body)), False),  # tuple
                ],
                False,
            ),
        ),
    )
    return head


def transformer_support_rule(rule_id: int, disjunction_id: int, rule_ast: ast.ASTType.Rule):
    """Returns the support rule, given the original rule.

    Args:
        rule_id (int): xclingo ID for the rule.
        rule_ast (ast.ASTType.Rule): original rule.

    Returns:
        ast.ASTType.Rule: the corresponding support rule.
    """
    head = _sup_head(rule_id, disjunction_id, rule_ast)
    body = list(_sup_body(rule_ast.body))

    return ast.Rule(loc, head, body)


def _fbody_head(rule_id: int, disjunction_id: int, rule_ast: ast.ASTType.Rule):
    """Returns the head of the fbody rule, given the original rule.

    Args:
        rule_id (int): xclingo ID for the rule.
        rule_ast (ast.ASTType.Rule): orinial rule.

    Returns:
        ast.AST: the head of the fbody rule.
    """ """"""
    return ast.Literal(
        loc,
        ast.Sign.NoSign,
        ast.SymbolicAtom(
            ast.Function(
                loc,
                "_xclingo_fbody",
                [
                    ast.SymbolicTerm(loc, Number(rule_id)),
                    ast.SymbolicTerm(loc, Number(disjunction_id)),
                    rule_ast.head.atom,
                    ast.Function(loc, "", list(collect_free_vars(rule_ast.body)), False),  # tuple
                ],
                False,
            ),
        ),
    )


def _fbody_body(lit_list: Sequence[ast.AST]):
    """Returns the body of the fbody rule, given the body of an original rule.

    Args:
        lit_list (Sequence[ast.AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        ast.AST: literals for the fbody rule.
    """
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
                                terms=list(_fbody_body(e.terms)),
                                condition=list(_fbody_body(e.condition)),
                            )
                            for e in lit.atom.elements
                        ],
                        right_guard=lit.atom.right_guard,
                    ),
                )

            else:
                yield lit

        elif lit.ast_type == ast.ASTType.ConditionalLiteral:
            yield ast.ConditionalLiteral(
                loc,
                literal=ast.Literal(
                    loc,
                    lit.literal.sign,
                    ast.SymbolicAtom(
                        ast.Function(
                            loc,
                            "_xclingo_f_atom",
                            [lit.literal.atom.symbol],
                            False,
                        )
                    ),
                ),
                condition=list(_sup_body(lit.condition)),
            )
        else:
            yield lit


def _xclingo_constraint_head(rule_id: int, lit_list: Sequence[ast.AST]):
    return ast.Literal(
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
                        list(propagates(lit_list)),
                        False,
                    ),  # tuple
                ],
                False,
            )
        ),
    )


def transformer_fbody_rule(rule_id: int, disjunction_id: int, rule_ast: ast.ASTType.Rule):
    """Returns the fbody rule, given the original rule.

    Args:
        rule_id (int): xclingo ID for the rule.
        rule_ast (ast.ASTType.Rule): original rule.

    Returns:
        ast.ASTType.Rule: the corresponding fbody rule.
    """
    head = _fbody_head(rule_id, disjunction_id, rule_ast)
    body = list(_fbody_body(rule_ast.body))
    return ast.Rule(loc, head, body)


def transformer_label_rule(
    rule_id: int,
    label_rule_ast: ast.ASTType.Rule,
    rule_body: Sequence[ast.AST],
):
    """Returns the final label rule, given the preliminary label rule (label_rule_ast) and the body of the original rule.

    Args:
        rule_id (int): xclingo ID for the rule that will be labelled.
        label_rule_ast (ast.ASTType.Rule): ast for the preliminary label rule.
        rule_body (Sequence[ast.AST]): body of the original rule (that is been labelled).

    Returns:
        ast.ASTType.Rule: final label rule.
    """ """"""
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
                        ast.Variable(loc, "DisID"),
                        head_var,
                        ast.Function(
                            loc,
                            "",
                            list(collect_free_vars(rule_body)),
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


def transformer_label_atom(rule_ast: ast.ASTType.Rule):
    """Translates the preliminary form of a label atom rule into its final form.

    Args:
        rule_ast (ast.ASTType.Rule): preliminary label atom rule.

    Returns:
        ast.ASTType.Rule: translated label atom rule.
    """ """"""
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
    body = list(_sup_body(rule_ast.body))
    rule = ast.Rule(loc, rule_ast.head, body)
    return rule


def transformer_show_trace(rule_ast: ast.ASTType.Rule):
    """Translates the preliminary form of a show trace rule into its final form.

    Args:
        rule_ast (ast.ASTType.Rule): preliminary show trace rule.

    Returns:
        ast.ASTType.rule: translated show trace rule.
    """
    literal_head = ast.Literal(
        loc,
        ast.Sign.NoSign,
        ast.SymbolicAtom(rule_ast.head.atom.symbol.arguments[0]),
    )
    rule = ast.Rule(loc, rule_ast.head, list(_sup_body(rule_ast.body)))
    return rule


def transformer_mute(rule_ast: ast.ASTType.Rule):
    """Translates the preliminary form of a mute rule into its final form.

    Args:
        rule_ast (ast.ASTType.Rule): preliminary mute rule.

    Returns:
        ast.ASTType.Rule: translated mute rule.
    """ """"""
    literal_head = ast.Literal(
        loc,
        ast.Sign.NoSign,
        ast.SymbolicAtom(rule_ast.head.atom.symbol.arguments[0]),
    )
    return ast.Rule(loc, rule_ast.head, list(_sup_body(rule_ast.body)))


def transformer_direct_cause(head: ast.ASTType.Literal, cause_candidates: Sequence[AST]):
    causes = [dep.atom.symbol.arguments[0] for dep in propagates(cause_candidates)]
    if causes:
        yield ast.Rule(
            location=loc,
            head=ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        "_xclingo_direct_cause",
                        [head.atom.symbol.arguments[2], ast.Pool(loc, causes)],
                        False,
                    )
                ),
            ),
            body=[
                ast.Literal(
                    loc,
                    ast.Sign.NoSign,
                    ast.SymbolicAtom(
                        ast.Function(
                            loc,
                            "_xclingo_f",
                            head.atom.symbol.arguments,
                            False,
                        )
                    ),
                )
            ],
        )
    for agg_elem in aggregates(cause_candidates):
        yield ast.Rule(
            location=loc,
            head=ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        "_xclingo_direct_cause",
                        [
                            head.atom.symbol.arguments[2],
                            ast.Pool(
                                loc,
                                [
                                    dep.atom.symbol.arguments[0]
                                    for dep in propagates(agg_elem.condition)
                                ],
                            ),
                        ],
                        False,
                    )
                ),
            ),
            body=list(agg_elem.condition)
            + [
                ast.Literal(
                    loc,
                    ast.Sign.NoSign,
                    ast.SymbolicAtom(
                        ast.Function(
                            loc,
                            "_xclingo_f",
                            head.atom.symbol.arguments,
                            False,
                        )
                    ),
                )
            ],
        )
    for cond_lit in conditional_literals(cause_candidates):
        yield ast.Rule(
            loc,
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        f"_xclingo_direct_cause",
                        [
                            head.atom.symbol.arguments[2],
                            ast.Pool(
                                loc,
                                [cond_lit.literal.atom.symbol.arguments[0]]
                                + [
                                    dep.atom.symbol.arguments[0]
                                    for dep in propagates(cond_lit.condition)
                                ],
                            ),
                        ],
                        False,
                    )
                ),
            ),
            body=list(cond_lit.condition)
            + [
                ast.Literal(
                    loc,
                    ast.Sign.NoSign,
                    ast.SymbolicAtom(
                        ast.Function(
                            loc,
                            "_xclingo_f",
                            head.atom.symbol.arguments,
                            False,
                        )
                    ),
                )
            ],
        )


def transformer_depends_rule(head: ast.ASTType.Literal, cause_candidates: Sequence[AST]):
    causes = [dep.atom.symbol.arguments[0] for dep in propagates(cause_candidates)]
    if causes:
        yield ast.Rule(
            loc,
            head=ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        f"_xclingo_sup_cause",
                        [head.atom.symbol, ast.Pool(loc, causes)],
                        False,
                    )
                ),
            ),
            body=[head],
        )
    for agg_elem in aggregates(cause_candidates):
        yield ast.Rule(
            loc,
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        f"_xclingo_sup_cause",
                        [
                            head.atom.symbol,
                            ast.Pool(
                                loc,
                                [
                                    dep.atom.symbol.arguments[0]
                                    for dep in propagates(agg_elem.condition)
                                ],
                            ),
                        ],
                        False,
                    )
                ),
            ),
            body=list(agg_elem.condition) + [head],
        )
    for cond_lit in conditional_literals(cause_candidates):
        yield ast.Rule(
            loc,
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        f"_xclingo_sup_cause",
                        [
                            head.atom.symbol,
                            ast.Pool(
                                loc,
                                [cond_lit.literal.atom.symbol.arguments[0]]
                                + [
                                    dep.atom.symbol.arguments[0]
                                    for dep in propagates(cond_lit.condition)
                                ],
                            ),
                        ],
                        False,
                    )
                ),
            ),
            body=list(cond_lit.condition) + [head],
        )
