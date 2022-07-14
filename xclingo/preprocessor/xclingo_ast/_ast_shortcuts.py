from typing import Sequence
from clingo.ast import AST, ASTType, Sign, Variable, BooleanConstant
from typing import Callable, Iterator, Sequence, Union
from clingo.ast import (
    AST,
    Location,
    Position,
    ASTType,
    Sign,
)
from clingo.ast import (
    Literal,
    SymbolicAtom,
    Function,
    BodyAggregate,
    BodyAggregateElement,
    ConditionalLiteral,
    SymbolicTerm,
    Pool,
    Variable,
)
from clingo import Number, String


loc = Location(
    Position("", 0, 0),
    Position("", 0, 0),
)

######### Body checks #########


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
            lit_list (Sequence[AST]): list of literal
    def wrapped_literal(wrapper_name: str, literal: AST):
        return literal(wrapper_name, [literal.atom.symbol], literal.sign)
    s to be processed. Normally
            a rule's body.

        Yields:
            AST: literals that are conditional literals.
    """
    for lit in lit_list:
        if lit.ast_type == ASTType.ConditionalLiteral:
            yield lit


def collect_free_vars(lit_list: Sequence[AST]):
    def collect_vars(lit: AST):
        if lit.atom.symbol.ast_type == ASTType.UnaryOperation:
            arguments = lit.atom.symbol.argument.arguments
        else:
            arguments = lit.atom.symbol.arguments
        for arg in arguments:
            if arg.ast_type == ASTType.Variable:
                yield str(arg.name)

    seen_vars, unsafe_vars = set(), set()
    for lit in lit_list:
        # handle conditional literals
        if lit.ast_type == ASTType.ConditionalLiteral:
            for var_name in collect_vars(lit.literal):
                unsafe_vars.add(var_name)
            continue

        # handle comparisons
        if lit.atom.ast_type == ASTType.Comparison:
            if lit.atom.left.ast_type == ASTType.Variable:
                seen_vars.add(str(lit.atom.left.name))
            if lit.atom.right.ast_type == ASTType.Variable:
                seen_vars.add(str(lit.atom.right.name))

        if lit.atom.ast_type == ASTType.BodyAggregate:
            if (
                lit.atom.left_guard is not None
                and lit.atom.left_guard.term.ast_type == ASTType.Variable
            ):
                seen_vars.add(str(lit.atom.left_guard.term.name))
            if (
                lit.atom.right_guard is not None
                and lit.atom.right_guard.term.ast_type == ASTType.Variable
            ):
                seen_vars.add(str(lit.atom.right_guard.term.name))

        # Skip negative literals
        elif lit.sign != Sign.NoSign:
            continue

        # handle positive body literals
        elif lit.atom.ast_type == ASTType.SymbolicAtom:
            for var_name in collect_vars(lit):
                seen_vars.add(var_name)
            continue

    for var_name in seen_vars:
        if var_name not in unsafe_vars:
            yield Variable(loc, var_name)


######### Check type of rule #########


def is_constraint(rule_ast):
    if rule_ast.ast_type == ASTType.Rule:
        if hasattr(rule_ast.head, "atom"):
            return (
                rule_ast.head.atom.ast_type == ASTType.BooleanConstant
                and rule_ast.head.atom == BooleanConstant(0)
            )
    return False


def is_choice_rule(rule_ast):
    return (
        rule_ast.ast_type == ASTType.Rule
        and rule_ast.head.ast_type == ASTType.Aggregate
        and hasattr(rule_ast.head, "function") == False
    )


def is_disyunctive_head(rule_ast):
    return rule_ast.head.ast_type == ASTType.Disjunction


def is_theory_head(rule_ast):
    return rule_ast.head.ast_type == ASTType.TheoryAtom


######### Shortcuts for creating ASTs #########


def handle_type(element: Union[AST, str, int, Sequence]):
    if isinstance(element, AST):
        if element.ast_type == ASTType.Literal:
            element = element.atom
        return element
    elif isinstance(element, str):
        return SymbolicTerm(loc, String(element))
    elif isinstance(element, int):
        return SymbolicTerm(loc, Number(element))
    elif hasattr(element, "__len__") and hasattr(element, "__getitem__"):
        return Function(loc, "", list([handle_type(item) for item in element]), False)
    else:
        raise ValueError("Unknown type: {}".format(type(element)))


def wrap_symbols(wrapper_name: str, symbols: Sequence):
    return SymbolicAtom(Function(loc, wrapper_name, [handle_type(item) for item in symbols], False))


def literal(func_name: str, args: Sequence, sign: Sign = Sign.NoSign):
    return Literal(
        loc,
        sign,
        wrap_symbols(func_name, args),
    )


def xclingo_dependency_head_literal(function_name: str, refernce_lit: AST, causes: Sequence[AST]):
    return literal(func_name=function_name, args=[refernce_lit, Pool(loc, causes)])


def xclingo_body_aggregate_literal(
    transformer_function: Callable[[Sequence[AST]], Iterator[AST]], lit: AST
):
    return Literal(
        loc,
        lit.sign,
        BodyAggregate(
            loc,
            left_guard=lit.atom.left_guard,
            function=lit.atom.function,
            elements=[
                BodyAggregateElement(
                    terms=list(transformer_function(e.terms)),
                    condition=list(transformer_function(e.condition)),
                )
                for e in lit.atom.elements
            ],
            right_guard=lit.atom.right_guard,
        ),
    )


def xclingo_conditional_literal(
    lit_wrapper: str,
    transformer_function: Callable[[Sequence[AST]], Iterator[AST]],
    conditional_literal: AST,
):
    return ConditionalLiteral(
        loc,
        literal=literal(
            lit_wrapper, [conditional_literal.literal], sign=conditional_literal.literal.sign
        ),
        condition=list(transformer_function(conditional_literal.condition)),
    )
