from typing import Callable, Iterator, Sequence

from clingo.ast import (
    AST,
    Location,
    Position,
    ASTType,
    Sign,
    ASTSequence,
)
from clingo.ast import (
    Literal,
    Rule,
    SymbolicAtom,
    Function,
    BodyAggregate,
    BodyAggregateElement,
    ConditionalLiteral,
    SymbolicTerm,
    Pool,
)
from clingo import (
    Number,
)

from ._transformers import (
    collect_free_vars,
    propagates,
)

########### Constants ###########

loc = Location(
    Position("", 0, 0),
    Position("", 0, 0),
)

_MODEL_WRAPPER = "_xclingo_model"
_F_ATOM_WRAPPER = "_xclingo_f_atom"
_F_WRAPPER = "_xclingo_f"

_SUP_HEAD = "_xclingo_sup"
_DEPENDS_HEAD = "_xclingo_sup_cause"
_FBODY_HEAD = "_xclingo_fbody"
_DIRECT_CAUSE_HEAD = "_xclingo_direct_cause"

########### Element types ###########


def xclingo_body_literal(wrapper_name: str, literal: AST):
    return Literal(
        loc,
        literal.sign,
        SymbolicAtom(Function(loc, wrapper_name, [literal.atom.symbol], False)),
    )


def xclingo_rule_head_literal(
    rule_id: int,
    disjunction_id: int,
    function_name: str,
    rule_head: AST,
    rule_body: Sequence[AST],
):
    return Literal(
        loc,
        Sign.NoSign,
        SymbolicAtom(
            Function(
                loc,
                function_name,
                [
                    SymbolicTerm(loc, Number(rule_id)),
                    SymbolicTerm(loc, Number(disjunction_id)),
                    rule_head.atom,
                    Function(loc, "", list(collect_free_vars(rule_body)), False),  # tuple
                ],
                False,
            )
        ),
    )


def xclingo_dependency_head_literal(
    location: Location, function_name: str, effect: AST, causes: Sequence[AST]
):
    return Literal(
        loc,
        Sign.NoSign,
        SymbolicAtom(
            Function(
                loc,
                function_name,
                [effect, Pool(loc, causes)],
                False,
            )
        ),
    )


def xclingo_body_aggregate_literal(
    transformer_function: Callable[[Sequence[AST]], Iterator[AST]], literal: AST
):
    return Literal(
        loc,
        literal.sign,
        BodyAggregate(
            loc,
            left_guard=literal.atom.left_guard,
            function=literal.atom.function,
            elements=[
                BodyAggregateElement(
                    terms=list(transformer_function(e.terms)),
                    condition=list(transformer_function(e.condition)),
                )
                for e in literal.atom.elements
            ],
            right_guard=literal.atom.right_guard,
        ),
    )


def xclingo_conditional_literal(
    lit_wrapper: str,
    transformer_function: Callable[[Sequence[AST]], Iterator[AST]],
    conditional_literal: AST,
):
    return ConditionalLiteral(
        loc,
        literal=xclingo_body_literal(lit_wrapper, conditional_literal.literal),
        condition=list(transformer_function(conditional_literal.condition)),
    )


########### Rule types ###########


class XclingoRule:
    def __init__(
        self, rule_id: int, disjunction_id: int, location: Location, head: AST, body: Sequence[AST]
    ):
        self._rule = Rule(
            location=loc,
            head=self.translate_head(rule_id, disjunction_id, head, body),
            body=list(self.translate_body(body)),
        )

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        raise NotImplementedError("This method is intended to be override")

    def translate_body(self, body: Sequence[AST]):
        raise NotImplementedError("This method is intended to be override")

    def get_rule(self):
        return self._rule


class SupportRule(XclingoRule):
    def __init__(
        self, rule_id: int, disjunction_id: int, location: Location, head: AST, body: Sequence[AST]
    ):
        super().__init__(rule_id, disjunction_id, location, head, body)

    def translate_body(self, body: Sequence[AST]):
        for lit in body:
            if lit.ast_type == ASTType.Literal:
                if lit.atom.ast_type == ASTType.SymbolicAtom:
                    yield xclingo_body_literal(_MODEL_WRAPPER, lit)

                elif lit.atom.ast_type == ASTType.BodyAggregate:
                    yield xclingo_body_aggregate_literal(self.translate_body, lit)

                else:
                    yield lit

            elif lit.ast_type == ASTType.ConditionalLiteral:
                yield xclingo_conditional_literal(_MODEL_WRAPPER, self.translate_body, lit)

            else:
                yield lit

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_rule_head_literal(rule_id, disjunction_id, _SUP_HEAD, head, body)


class FRule(XclingoRule):
    def __init__(
        self, rule_id: int, disjunction_id: int, location: Location, head: AST, body: Sequence[AST]
    ):
        super().__init__(rule_id, disjunction_id, location, head, body)

    def translate_body(self, body: Sequence[AST]):
        for lit in body:
            if lit.ast_type == ASTType.Literal:
                if lit.atom.ast_type == ASTType.SymbolicAtom:
                    if lit.sign == Sign.NoSign:
                        yield xclingo_body_literal(_F_ATOM_WRAPPER, lit)
                    else:
                        yield xclingo_body_literal(_MODEL_WRAPPER, lit)

                elif lit.atom.ast_type == ASTType.BodyAggregate:
                    yield xclingo_body_aggregate_literal(self.translate_body, lit)

                else:
                    yield lit

            elif lit.ast_type == ASTType.ConditionalLiteral:
                yield xclingo_conditional_literal(_F_ATOM_WRAPPER, self.translate_body, lit)
            else:
                yield lit

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_rule_head_literal(rule_id, disjunction_id, _FBODY_HEAD, head, body)


class DependsRule(SupportRule):
    def __init__(
        self,
        rule_id: int,
        disjunction_id: int,
        location: Location,
        head: AST,
        body: Sequence[AST],
        cause_candidates: Sequence[AST],
    ):
        self.causes = propagates(cause_candidates)
        self.sup_lit = super().translate_head(head, body)
        super().__init__(rule_id, disjunction_id, location, head, body)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_dependency_head_literal(_DEPENDS_HEAD, self.sup_lit, self.causes)

    def translate_body(self, body: Sequence[AST]):
        for lit in super().translate_body(self.causes):
            yield lit
        yield self.sup_lit


# class DirectCauseRule(FRule):
#     def __init__(
#         self,
#         rule_id: int,
#         disjunction_id: int,
#         location: Location,
#         head: AST,
#         body: Sequence[AST],
#         cause_candidates: Sequence[AST],
#     ):
#         self.causes = propagates(cause_candidates)
#         self.__head = head
#         self.rule_id = rule_id
#         self.disjunction_id = disjunction_id

#     def translate_head(self, head: AST, body: Sequence[AST]):
#         return XclingoDependencyHeadLiteral(_DEPENDS_HEAD, head, self.causes)

#     def translate_body(self, body: Sequence[AST]):
#         for lit in super().translate_body(self.causes):
#             yield lit
#         yield xclingo_rule_head_literal(
#             self.rule_id, self.disjunction_id, _F_WRAPPER, self.__head, body
#         )
