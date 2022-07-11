from trace import Trace
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

from ._transformers import (
    collect_free_vars,
    propagates,
    aggregates,
    conditional_literals,
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


class SupportRule(ModelBody, SupLit, XclingoRule):
    def __init__(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST], **kwargs):
        super().__init__(
            rule_id=rule_id, disjunction_id=disjunction_id, head=head, body=body, **kwargs
        )

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return self._reference_lit


class FBodyRule(FiredBody, FbodyLit, XclingoRule):
    def __init__(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST], **kwargs):
        super().__init__(
            rule_id=rule_id, disjunction_id=disjunction_id, head=head, body=body, **kwargs
        )

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return self._reference_lit


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


class TraceAnnotation:
    def __init__(self, labelled: AST, label: AST, vars: Sequence[AST], **kwargs):
        self.labelled = labelled
        self.label = label
        self.vars = vars
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_label_head_literal(self.labelled, self.label, self.vars)


class TraceAnnotationRule(TraceAnnotation, ModelBody, XclingoRule):
    def __init__(self, location: Location, head: AST, body: Sequence[AST]):
        super().__init__(
            labelled=head.elements[0].terms[0],
            label=head.elements[0].terms[1],
            vars=head.elements[0].terms[2:],
            rule_id=None,
            disjunction_id=None,
            location=location,
            head=head,
            body=body,
        )


class TraceRuleAnnotationRule(TraceAnnotation, FiredBody, FLit, XclingoRule):
    def __init__(self, rule_id: int, head: AST, body: Sequence[AST], trace_head: AST):
        super().__init__(
            labelled=Variable(loc, "Head"),
            label=trace_head.elements[0].terms[0],
            vars=trace_head.elements[0].terms[1:],
            rule_id=rule_id,
            disjunction_id=Variable(loc, "DisID"),
            location=None,
            head=Variable(loc, "Head"),
            body=body,
        )

    def translate_body(self, body: Sequence[AST]):
        yield self._reference_lit


class MarkAnnotation(ModelBody, XclingoRule):
    def __init__(self, wrapper: str, location: Location, head: AST, body: Sequence[AST]):
        self._wrapper = wrapper
        super().__init__(rule_id=None, disjunction_id=None, location=location, head=head, body=body)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_positive_literal(self._wrapper, head.elements[0].terms[0])


class ShowTraceAnnotationRule(MarkAnnotation):
    def __init__(self, location: Location, head: AST, body: Sequence[AST]):
        super().__init__(wrapper=_SHOW_TRACE_HEAD, location=location, head=head, body=body)


class MuteAnnotationRule(MarkAnnotation):
    def __init__(self, location: Location, head: AST, body: Sequence[AST]):
        super().__init__(wrapper=_MUTE_HEAD, location=location, head=head, body=body)


######### Translators ##########


class AnnotationTranslator:
    def __init__(self):
        pass

    def translate(self, annotation_name: str, rule_ast: AST):
        if annotation_name == "show_trace":
            yield ShowTraceAnnotationRule(None, rule_ast.head, rule_ast.body).get_rule()
        elif annotation_name == "trace":
            yield TraceAnnotationRule(None, rule_ast.head, rule_ast.body).get_rule()
        elif annotation_name == "mute":
            yield MuteAnnotationRule(None, rule_ast.head, rule_ast.body).get_rule()


class RuleTranslator:
    def __init__(self, rule, depends, trace_rule) -> None:
        self._rule = rule
        self._depends = depends
        self._trace_rule = trace_rule

    def translate(
        self, rule_id, disjunction_id, rule_ast: AST, trace_rule_ast: AST
    ) -> Sequence[AST]:
        yield self._rule(
            rule_id=rule_id,
            disjunction_id=disjunction_id,
            location=None,
            head=rule_ast.head,
            body=rule_ast.body,
        ).get_rule()
        if rule_ast.body:
            causes = list(propagates(rule_ast.body))
            if causes:
                yield self._depends(
                    rule_id=rule_id,
                    disjunction_id=disjunction_id,
                    location=None,
                    head=rule_ast.head,
                    body=rule_ast.body,
                    extra_body=[],
                    causes=causes,
                ).get_rule()
        for agg_element in aggregates(rule_ast.body):
            causes = list(propagates(agg_element.condition))
            if causes:
                yield self._depends(
                    rule_id=rule_id,
                    disjunction_id=disjunction_id,
                    location=None,
                    head=rule_ast.head,
                    body=rule_ast.body,
                    extra_body=agg_element.condition,
                    causes=causes,
                ).get_rule()
        for cond_lit in conditional_literals(rule_ast.body):
            causes = list(propagates(cond_lit.condition))
            if causes:
                yield self._depends(
                    rule_id=rule_id,
                    disjunction_id=disjunction_id,
                    location=None,
                    head=rule_ast.head,
                    body=rule_ast.body,
                    extra_body=cond_lit.condition,
                    causes=causes,
                ).get_rule()
        if self._trace_rule is not None and trace_rule_ast is not None:
            yield self._trace_rule(
                rule_id, rule_ast.head, rule_ast.body, trace_rule_ast.head
            ).get_rule()


class SupportTranslator(RuleTranslator):
    def __init__(self) -> None:
        super().__init__(SupportRule, DependsRule, None)


class FTranslator(RuleTranslator):
    def __init__(self) -> None:
        super().__init__(FBodyRule, DirectCauseRule, TraceRuleAnnotationRule)
