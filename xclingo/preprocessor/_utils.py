import re
from clingo import ast

loc = ast.Location(
    ast.Position("", 0, 0),
    ast.Position("", 0, 0),
)


def translate_trace(theory_trace_rule: ast.AST):
    theory_terms = theory_trace_rule.head.elements[0].terms
    return ast.Rule(
        location=loc,
        head=ast.Literal(
            location=loc,
            sign=ast.Sign.NoSign,
            atom=ast.SymbolicAtom(
                ast.Function(
                    location=loc,
                    name="_xclingo_label",
                    arguments=[
                        ast.Function(loc, "id", [], False),
                        ast.Function(
                            location=loc,
                            name="label",
                            arguments=[
                                theory_terms[0],
                                ast.Function(loc, "", theory_terms[1:], False),
                            ],
                            external=True,
                        ),
                    ],
                    external=False,
                )
            ),
        ),
        body=[],
    )


def translate_trace_all(theory_trace_rule: ast.AST):
    theory_terms = theory_trace_rule.head.elements[0].terms
    return ast.Rule(
        location=loc,
        head=ast.Literal(
            location=loc,
            sign=ast.Sign.NoSign,
            atom=ast.SymbolicAtom(
                ast.Function(
                    location=loc,
                    name="_xclingo_label",
                    arguments=[
                        theory_terms[0],
                        ast.Function(
                            location=loc,
                            name="label",
                            arguments=[
                                theory_terms[1],
                                ast.Function(loc, "", theory_terms[2:], False),
                            ],
                            external=True,
                        ),
                    ],
                    external=False,
                )
            ),
        ),
        body=theory_trace_rule.body,
    )


def translate_show_all(theory_trace_rule: ast.AST):
    theory_terms = theory_trace_rule.head.elements[0].terms
    return ast.Rule(
        location=loc,
        head=ast.Literal(
            location=loc,
            sign=ast.Sign.NoSign,
            atom=ast.SymbolicAtom(
                ast.Function(
                    location=loc,
                    name="_xclingo_show_trace",
                    arguments=[theory_terms[0]],
                    external=False,
                )
            ),
        ),
        body=theory_trace_rule.body,
    )


def translate_mute(theory_trace_rule: ast.AST):
    theory_terms = theory_trace_rule.head.elements[0].terms
    return ast.Rule(
        location=loc,
        head=ast.Literal(
            location=loc,
            sign=ast.Sign.NoSign,
            atom=ast.SymbolicAtom(
                ast.Function(
                    location=loc,
                    name="_xclingo_muted",
                    arguments=[theory_terms[0]],
                    external=False,
                )
            ),
        ),
        body=theory_trace_rule.body,
    )


def is_constraint(rule_ast):
    if rule_ast.ast_type == ast.ASTType.Rule:
        if hasattr(rule_ast.head, "atom"):
            return (
                rule_ast.head.atom.ast_type == ast.ASTType.BooleanConstant
                and rule_ast.head.atom == ast.BooleanConstant(0)
            )
    return False


def is_xclingo_label(rule_ast):
    return (
        rule_ast.ast_type == ast.ASTType.Rule
        and rule_ast.head.ast_type == ast.ASTType.Literal
        and rule_ast.head.atom != ast.BooleanConstant(0)
        and rule_ast.head.atom.symbol.ast_type == ast.ASTType.Function
        and rule_ast.head.atom.symbol.name == "_xclingo_label"
    )


def is_xclingo_show_trace(rule_ast):
    return (
        rule_ast.ast_type == ast.ASTType.Rule
        and rule_ast.head.ast_type == ast.ASTType.Literal
        and rule_ast.head.atom != ast.BooleanConstant(0)
        and rule_ast.head.atom.symbol.ast_type == ast.ASTType.Function
        and rule_ast.head.atom.symbol.name == "_xclingo_show_trace"
    )


def is_xclingo_mute(rule_ast):
    return (
        rule_ast.ast_type == ast.ASTType.Rule
        and rule_ast.head.ast_type == ast.ASTType.Literal
        and rule_ast.head.atom != ast.BooleanConstant(0)
        and rule_ast.head.atom.symbol.ast_type == ast.ASTType.Function
        and rule_ast.head.atom.symbol.name == "_xclingo_muted"
    )


def is_label_rule(rule_ast):
    # Precondition: is_xclingo_label(rule_ast) == True
    return str(rule_ast.head.atom.symbol.arguments[0]) == "id"


def is_choice_rule(rule_ast):
    return (
        rule_ast.ast_type == ast.ASTType.Rule
        and rule_ast.head.ast_type == ast.ASTType.Aggregate
        and hasattr(rule_ast.head, "function") == False
    )


def is_disyunctive_head(rule_ast):
    return rule_ast.head.ast_type == ast.ASTType.Disjunction
