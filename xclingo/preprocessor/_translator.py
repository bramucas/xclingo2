from clingo.ast import AST, Location, Position
from typing import Sequence

from .xclingo_ast import (
    ShowTraceAnnotationRule,
    TraceAnnotationRule,
    MuteAnnotationRule,
    MuteRuleAnnotation,
    SupportRule,
    DependsRule,
    TraceRuleAnnotationRule,
    RelaxedConstraint,
)
from .xclingo_ast import (
    propagates,
    aggregates,
    conditional_literals,
)
from enum import Enum

# TODO: fix location
loc = Location(
    Position("", 0, 0),
    Position("", 0, 0),
)


class RelaxedConstraintTranslator:
    def __init__(self) -> None:
        pass

    def translate(self, rule_id: int, constraint_ast: AST):
        yield RelaxedConstraint(
            location=None,
            disjunction_id=None,
            rule_id=rule_id,
            head=constraint_ast.head,
            body=constraint_ast.body,
        ).get_ast()


class AnnotationNames(dict):
    _SHOW_TRACE = "show_trace"
    _TRACE = "trace"
    _TRACE_RULE = "trace_rule"
    _MUTE = "mute"
    _MUTE_BODY = "mute_body"

    @staticmethod
    def all():
        return [
            v for k, v in AnnotationNames.__dict__.items() if not k.startswith("__") and k != "all"
        ]


class AnnotationTranslator:
    def __init__(self):
        self._annotation_asts = {
            AnnotationNames._SHOW_TRACE: ShowTraceAnnotationRule,
            AnnotationNames._TRACE: TraceAnnotationRule,
            AnnotationNames._MUTE: MuteAnnotationRule,
            AnnotationNames._MUTE_BODY: MuteRuleAnnotation,
        }

    def translate(self, annotation_name: str, rule_ast: AST, rule_id: int):
        if annotation_name in self._annotation_asts:
            yield self._annotation_asts[annotation_name](
                location=None,
                head=rule_ast.head,
                body=rule_ast.body,
                rule_id=rule_id,
                disjunction_id=None,
            ).get_ast()
        else:
            raise RuntimeError(f"Unknown annotation name: {annotation_name}")


class RuleTranslator:
    def __init__(self, rule, depends, trace_rule) -> None:
        self._rule = rule
        self._depends = depends
        self._trace_rule = trace_rule

    def translate(
        self, rule_id, disjunction_id, rule_head: AST, rule_body: Sequence[AST], trace_rule_ast: AST
    ) -> Sequence[AST]:
        yield self._rule(
            rule_id=rule_id,
            disjunction_id=disjunction_id,
            location=None,
            head=rule_head,
            body=rule_body,
        ).get_ast()
        if rule_body:
            causes = list(propagates(rule_body))
            if causes:
                yield self._depends(
                    rule_id=rule_id,
                    disjunction_id=disjunction_id,
                    location=None,
                    head=rule_head,
                    body=rule_body,
                    extra_body=[],
                    causes=causes,
                ).get_ast()
        for agg_element in aggregates(rule_body):
            causes = list(propagates(agg_element.condition))
            if causes:
                yield self._depends(
                    rule_id=rule_id,
                    disjunction_id=disjunction_id,
                    location=None,
                    head=rule_head,
                    body=rule_body,
                    extra_body=agg_element.condition,
                    causes=causes,
                ).get_ast()
        for cond_lit in conditional_literals(rule_body):
            causes = list(propagates(cond_lit.condition))
            yield self._depends(
                rule_id=rule_id,
                disjunction_id=disjunction_id,
                location=None,
                head=rule_head,
                body=rule_body,
                extra_body=cond_lit.condition,
                causes=[cond_lit.literal] + causes,
            ).get_ast()
        if self._trace_rule is not None and trace_rule_ast is not None:
            yield self._trace_rule(
                rule_id=rule_id,
                location=None,
                body=rule_body,
                trace_head=trace_rule_ast.head,
            ).get_ast()


class SupportTranslator(RuleTranslator):
    def __init__(self) -> None:
        super().__init__(SupportRule, DependsRule, TraceRuleAnnotationRule)
