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
    Rule,
    SymbolicAtom,
    Function,
    BodyAggregate,
    BodyAggregateElement,
    ConditionalLiteral,
    SymbolicTerm,
    Pool,
    Variable,
)
from clingo import (
    Number,
)

from ._utils import (
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


_SHOW_TRACE_HEAD = "_xclingo_show_trace"
_MUTE_HEAD = "_xclingo_muted"
_TRACE_HEAD = "_xclingo_label"

_SUP_HEAD = "_xclingo_sup"
_DEPENDS_HEAD = "_xclingo_sup_cause"
_FBODY_HEAD = "_xclingo_fbody"
_F_HEAD = "_xclingo_f"
_DIRECT_CAUSE_HEAD = "_xclingo_direct_cause"
_XCLINGO_CONSTRAINT_HEAD = "_xclingo_violated_constraint"

########### Element types ###########


def xclingo_wrap_symbols(wrapper_name: str, symbols: AST):
    return SymbolicAtom(Function(loc, wrapper_name, symbols, False))


def xclingo_positive_literal(wrapper_name: str, symbol: AST):
    return Literal(
        loc,
        Sign.NoSign,
        xclingo_wrap_symbols(wrapper_name, [symbol]),
    )


def xclingo_body_literal(wrapper_name: str, literal: AST):
    return Literal(
        loc,
        literal.sign,
        xclingo_wrap_symbols(wrapper_name, [literal.atom.symbol]),
    )


def xclingo_constraint_head(rule_id: int, body: Sequence[AST]):
    return Literal(
        loc,
        Sign.NoSign,
        xclingo_wrap_symbols(
            _XCLINGO_CONSTRAINT_HEAD,
            [
                SymbolicTerm(loc, Number(rule_id)),
                Function(loc, "", list(collect_free_vars(body)), False),
            ],
        ),
    )


def xclingo_label_head_literal(labelled: AST, label: AST, vars: Sequence[AST]):
    external_func = Function(
        location=loc,
        name="label",
        arguments=[label, Function(loc, "", vars, False)],
        external=True,
    )
    return Literal(
        loc,
        Sign.NoSign,
        xclingo_wrap_symbols(_TRACE_HEAD, [labelled, external_func]),
    )


def xclingo_rule_head_literal(
    rule_id: Union[int, AST],
    disjunction_id: Union[int, AST],
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
                    SymbolicTerm(loc, Number(rule_id)) if isinstance(rule_id, int) else rule_id,
                    SymbolicTerm(loc, Number(disjunction_id))
                    if isinstance(disjunction_id, int)
                    else disjunction_id,
                    rule_head.atom if rule_head.ast_type == ASTType.Literal else rule_head,
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


####### Reference Lit


class ReferenceLit:
    def __init__(
        self,
        func_name: str,
        rule_id: Union[int, AST],
        disjunction_id: Union[int, AST],
        head: AST,
        body: Sequence[AST],
        **kwargs,
    ):
        self._reference_lit = xclingo_rule_head_literal(
            rule_id, disjunction_id, func_name, head, body
        )
        super().__init__(
            rule_id=rule_id, disjunction_id=disjunction_id, head=head, body=body, **kwargs
        )


class SupLit(ReferenceLit):
    def __init__(self, **kwargs):
        super().__init__(func_name=_SUP_HEAD, **kwargs)


class FbodyLit(ReferenceLit):
    def __init__(self, **kwargs):
        super().__init__(func_name=_FBODY_HEAD, **kwargs)


class FLit(ReferenceLit):
    def __init__(self, **kwargs):
        super().__init__(func_name=_F_HEAD, **kwargs)


####### Bodies


class DoNothingBody:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def translate_body(self, body: Sequence[AST]):
        for lit in body:
            yield lit


class ModelBody:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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


class FiredBody:
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

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


####### Rules


class SupportRule(ModelBody, SupLit, XclingoRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return self._reference_lit


class FBodyRule(FiredBody, FbodyLit, XclingoRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return self._reference_lit


class RelaxedConstraint(DoNothingBody, XclingoRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_constraint_head(rule_id, body)


####### Depends


class Depends:
    def __init__(self, extra_body: Sequence[AST], causes: Sequence[AST], **kwargs):
        self._extra_body = extra_body
        self._causes = causes
        super().__init__(**kwargs)

    def translate_body(self, body: Sequence[AST]):
        for lit in super().translate_body(self._extra_body):
            yield lit
        yield self._reference_lit


class DependsRule(Depends, ModelBody, SupLit, XclingoRule):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_dependency_head_literal(
            None, _DEPENDS_HEAD, self._reference_lit, self._causes
        )


class DirectCauseRule(Depends, FiredBody, FLit, XclingoRule):
    def __init__(
        self,
        **kwargs,
    ):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_dependency_head_literal(None, _DIRECT_CAUSE_HEAD, head, self._causes)


####### Traces


class TraceAnnotation:
    def __init__(self, labelled: AST, label: AST, vars: Sequence[AST], **kwargs):
        self.labelled = labelled
        self.label = label
        self.vars = vars
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_label_head_literal(self.labelled, self.label, self.vars)


class TraceAnnotationRule(TraceAnnotation, ModelBody, XclingoRule):
    def __init__(self, head: AST, **kwargs):
        super().__init__(
            labelled=head.elements[0].terms[0],
            label=head.elements[0].terms[1],
            vars=head.elements[0].terms[2:],
            rule_id=None,
            disjunction_id=None,
            head=head,
            **kwargs,
        )


class TraceRuleAnnotationRule(TraceAnnotation, FiredBody, FLit, XclingoRule):
    def __init__(self, trace_head: AST, **kwargs):
        super().__init__(
            labelled=Variable(loc, "Head"),
            label=trace_head.elements[0].terms[0],
            vars=trace_head.elements[0].terms[1:],
            disjunction_id=Variable(loc, "DisID"),
            location=None,
            head=Variable(loc, "Head"),
            **kwargs,
        )

    def translate_body(self, body: Sequence[AST]):
        yield self._reference_lit


####### Annotations that mark atoms


class MarkAnnotation(ModelBody, XclingoRule):
    def __init__(self, wrapper: str, **kwargs):
        self._wrapper = wrapper
        super().__init__(rule_id=None, disjunction_id=None, **kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_positive_literal(self._wrapper, head.elements[0].terms[0])


class ShowTraceAnnotationRule(MarkAnnotation):
    def __init__(self, **kwargs):
        super().__init__(wrapper=_SHOW_TRACE_HEAD, **kwargs)


class MuteAnnotationRule(MarkAnnotation):
    def __init__(self, **kwargs):
        super().__init__(wrapper=_MUTE_HEAD, **kwargs)
