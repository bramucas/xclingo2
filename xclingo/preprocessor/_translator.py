from clingo.ast import AST, Location, Position
from typing import Sequence

from .xclingo_ast import (
    ShowTraceAnnotationRule,
    TraceAnnotationRule,
    MuteAnnotationRule,
    SupportRule,
    DependsRule,
    FBodyRule,
    DirectCauseRule,
    TraceRuleAnnotationRule,
    RelaxedConstraint,
)
from .xclingo_ast import (
    propagates,
    aggregates,
    conditional_literals,
)

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


class AnnotationTranslator:
    def __init__(self):
        pass

    def translate(self, annotation_name: str, rule_ast: AST):
        if annotation_name == "show_trace":
            yield ShowTraceAnnotationRule(
                location=None, head=rule_ast.head, body=rule_ast.body
            ).get_ast()
        elif annotation_name == "trace":
            yield TraceAnnotationRule(
                location=None, head=rule_ast.head, body=rule_ast.body
            ).get_ast()
        elif annotation_name == "mute":
            yield MuteAnnotationRule(
                location=None, head=rule_ast.head, body=rule_ast.body
            ).get_ast()


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
                body=rule_body,
                trace_head=trace_rule_ast.head,
            ).get_ast()


class SupportTranslator(RuleTranslator):
    def __init__(self) -> None:
        super().__init__(SupportRule, DependsRule, TraceRuleAnnotationRule)


class FTranslator(RuleTranslator):
    def __init__(self) -> None:
        super().__init__(FBodyRule, DirectCauseRule, TraceRuleAnnotationRule)
