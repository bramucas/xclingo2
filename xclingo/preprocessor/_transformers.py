from clingo.ast import AST, Location, Position
from typing import Sequence

from ._utils import (
    propagates,
    aggregates,
    conditional_literals,
)

from ._xclingo_ast import (
    ShowTraceAnnotationRule,
    TraceAnnotationRule,
    MuteAnnotationRule,
    SupportRule,
    DependsRule,
    FBodyRule,
    DirectCauseRule,
    TraceRuleAnnotationRule,
)

# TODO: fix location
loc = Location(
    Position("", 0, 0),
    Position("", 0, 0),
)


class AnnotationTranslator:
    def __init__(self):
        pass

    def translate(self, annotation_name: str, rule_ast: AST):
        if annotation_name == "show_trace":
            yield ShowTraceAnnotationRule(
                location=None, head=rule_ast.head, body=rule_ast.body
            ).get_rule()
        elif annotation_name == "trace":
            yield TraceAnnotationRule(
                location=None, head=rule_ast.head, body=rule_ast.body
            ).get_rule()
        elif annotation_name == "mute":
            yield MuteAnnotationRule(
                location=None, head=rule_ast.head, body=rule_ast.body
            ).get_rule()


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
            yield self._depends(
                rule_id=rule_id,
                disjunction_id=disjunction_id,
                location=None,
                head=rule_ast.head,
                body=rule_ast.body,
                extra_body=cond_lit.condition,
                causes=[cond_lit.literal] + causes,
            ).get_rule()
        if self._trace_rule is not None and trace_rule_ast is not None:
            yield self._trace_rule(
                rule_id=rule_id,
                body=rule_ast.body,
                trace_head=trace_rule_ast.head,
            ).get_rule()


class SupportTranslator(RuleTranslator):
    def __init__(self) -> None:
        super().__init__(SupportRule, DependsRule, None)


class FTranslator(RuleTranslator):
    def __init__(self) -> None:
        super().__init__(FBodyRule, DirectCauseRule, TraceRuleAnnotationRule)
