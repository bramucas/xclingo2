from typing import Sequence

from clingo.ast import AST, ASTType, Sign, Variable

from clingo import ast

loc = ast.Location(
    ast.Position("", 0, 0),
    ast.Position("", 0, 0),
)


def propagates(lit_list: Sequence[AST]):
    """Captures the part of a body that propagate causes.
    This is, the positive part of the body of a rule. Comparison literals are ignored.

    Args:
        lit_list (Sequence[AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        AST: literals that propagate cause.
    """
    for lit in lit_list:
        if (
            lit.ast_type != ASTType.ConditionalLiteral
            and lit.sign == Sign.NoSign
            and lit.atom.ast_type == ASTType.SymbolicAtom
        ):
            yield lit


def aggregates(lit_list: Sequence[AST]):
    """Captures the part of a body that is an aggregate.

    Args:
        lit_list (Sequence[AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        AST: literals that are aggregates.
    """
    for lit in lit_list:
        if (
            lit.ast_type != ASTType.ConditionalLiteral
            and lit.sign == Sign.NoSign
            and lit.atom.ast_type == ASTType.BodyAggregate
        ):
            for e in lit.atom.elements:
                yield e


def conditional_literals(lit_list: Sequence[AST]):
    """Captures the part of a body that is a conditional literal.

    Args:
        lit_list (Sequence[AST]): list of literals to be processed. Normally
        a rule's body.

    Yields:
        AST: literals that are conditional literals.
    """
    for lit in lit_list:
        if lit.ast_type == ASTType.ConditionalLiteral:
            yield lit


def collect_free_vars(lit_list: Sequence[AST]):
    seen_vars, unsafe_vars = set(), set()
    for lit in lit_list:
        # handle conditional literals
        if lit.ast_type == ASTType.ConditionalLiteral:
            for arg in lit.literal.atom.symbol.arguments:
                if arg.ast_type == ASTType.Variable:
                    unsafe_vars.add(str(arg.name))
            continue

        # handle comparisons
        if lit.atom.ast_type == ASTType.Comparison:
            if lit.atom.left.ast_type == ASTType.Variable:
                seen_vars.add(str(lit.atom.left.name))
            if lit.atom.right.ast_type == ASTType.Variable:
                seen_vars.add(str(lit.atom.right.name))

        # Skip negative literals
        elif lit.sign != Sign.NoSign:
            continue

        # handle positive body literals
        elif lit.atom.ast_type == ASTType.SymbolicAtom:
            for arg in lit.atom.symbol.arguments:
                if arg.ast_type == ASTType.Variable:
                    seen_vars.add(str(arg.name))
            continue

    for var_name in seen_vars:
        if var_name not in unsafe_vars:
            yield Variable(loc, var_name)


def is_constraint(rule_ast):
    if rule_ast.ast_type == ast.ASTType.Rule:
        if hasattr(rule_ast.head, "atom"):
            return (
                rule_ast.head.atom.ast_type == ast.ASTType.BooleanConstant
                and rule_ast.head.atom == ast.BooleanConstant(0)
            )
    return False


def xclingo_annotation(rule_ast):
    if rule_ast.ast_type == ast.ASTType.Rule and rule_ast.head.ast_type == ast.ASTType.TheoryAtom:
        if rule_ast.head.term.name in ["show_trace", "trace", "mute", "trace_rule"]:
            return rule_ast.head.term.name
    return None


def is_choice_rule(rule_ast):
    return (
        rule_ast.ast_type == ast.ASTType.Rule
        and rule_ast.head.ast_type == ast.ASTType.Aggregate
        and hasattr(rule_ast.head, "function") == False
    )


def is_disyunctive_head(rule_ast):
    return rule_ast.head.ast_type == ast.ASTType.Disjunction
