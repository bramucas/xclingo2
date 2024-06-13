from typing import Sequence, Union
from clingo import TheoryTerm
from clingo.ast import (
    AST,
    Location,
    ASTType,
    Sign,
)
from clingo.ast import (
    Rule,
    Variable,
    Function,
)
from ._ast_shortcuts import (
    xclingo_dependency_head_literal,
    xclingo_body_aggregate_literal,
    xclingo_conditional_literal,
    literal,
    collect_free_vars,
    loc,
)

########### Constants ###########

_SHOW_TRACE_HEAD = "_xclingo_show_trace"
_MUTE_HEAD = "_xclingo_muted"
_MUTE_RULE_HEAD = "_xclingo_muted_body"
_TRACE_HEAD = "_xclingo_label"

_MODEL_WRAPPER = "_xclingo_model"
_SUP_HEAD = "_xclingo_sup"
_DEPENDS_HEAD = "_xclingo_depends"
_F_HEAD = "_xclingo_f"
_XCLINGO_CONSTRAINT_HEAD = "_xclingo_violated_constraint"


########### Rule types ###########


class XclingoAST:
    def __init__(self):
        pass

    def get_ast(self):
        return self._ast


class XclingoRule(XclingoAST):
    def __init__(
        self, rule_id: int, disjunction_id: int, location: Location, head: AST, body: Sequence[AST]
    ):
        self._ast = Rule(
            location=loc,
            head=self.translate_head(rule_id, disjunction_id, head, body),
            body=list(self.translate_body(body)),
        )

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        raise NotImplementedError("This method is intended to be override")

    def translate_body(self, body: Sequence[AST]):
        raise NotImplementedError("This method is intended to be override")


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
        self._reference_lit = literal(
            func_name,
            [rule_id, disjunction_id, head, list(collect_free_vars(body))],
        )
        super().__init__(
            rule_id=rule_id, disjunction_id=disjunction_id, head=head, body=body, **kwargs
        )


class SupLit(ReferenceLit):
    def __init__(self, **kwargs):
        super().__init__(func_name=_SUP_HEAD, **kwargs)


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
                    yield literal(_MODEL_WRAPPER, [lit], sign=lit.sign)

                elif lit.atom.ast_type == ASTType.BodyAggregate:
                    yield xclingo_body_aggregate_literal(self.translate_body, lit)

                else:
                    yield lit

            elif lit.ast_type == ASTType.ConditionalLiteral:
                yield xclingo_conditional_literal(_MODEL_WRAPPER, self.translate_body, lit)

            else:
                yield lit


####### Rules


class SupportRule(ModelBody, SupLit, XclingoRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return self._reference_lit


class RelaxedConstraint(DoNothingBody, XclingoRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return literal(
            _XCLINGO_CONSTRAINT_HEAD, [rule_id, list(collect_free_vars(body))], sign=Sign.NoSign
        )


class DependsRule(ModelBody, SupLit, XclingoRule):
    def __init__(self, extra_body: Sequence[AST], causes: Sequence[AST], **kwargs):
        self._extra_body = extra_body
        self._causes = causes
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return xclingo_dependency_head_literal(_DEPENDS_HEAD, self._reference_lit, self._causes)

    def translate_body(self, body: Sequence[AST]):
        for lit in super().translate_body(self._extra_body):
            yield lit
        yield self._reference_lit


####### Annotations that mark atoms
class AutoSafeTheory:
    def __init__(self, head: AST, body: Sequence[AST], **kwargs):
        # We need the name and the arguments of the symbol to be able to create the annotation
        term = head.elements[0].terms[0]
        if term.ast_type == ASTType.SymbolicTerm:
            name, args = term.symbol.name, term.symbol.arguments
        elif term.ast_type == ASTType.TheoryUnparsedTerm:  # strong negation
            args = term.elements[0].term.arguments
            if len(term.elements[0].operators) == 1 and term.elements[0].operators[0] == "-":
                name = "-" + term.elements[0].term.name
            else:
                name = term.elements[0].term.name
        else:
            name, args = term.name, term.arguments

        super().__init__(
            head=head,
            body=[literal(name, args)] + list(body),
            **kwargs,
        )


class MarkAnnotation(AutoSafeTheory, ModelBody, XclingoRule):
    def __init__(self, wrapper: str, **kwargs):
        self._wrapper = wrapper
        super().__init__(
            **kwargs,
        )

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return literal(self._wrapper, [head.elements[0].terms[0]], sign=Sign.NoSign)


class ShowTraceAnnotationRule(MarkAnnotation):
    def __init__(self, **kwargs):
        super().__init__(wrapper=_SHOW_TRACE_HEAD, **kwargs)


class MuteAnnotationRule(MarkAnnotation):
    def __init__(self, **kwargs):
        super().__init__(wrapper=_MUTE_HEAD, **kwargs)


####### MarkRule


class MuteRuleAnnotation(DoNothingBody, XclingoRule):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        return literal(_MUTE_RULE_HEAD, [rule_id], sign=Sign.NoSign)


####### Traces


class TraceAnnotation:
    def __init__(self, labelled: AST, label: AST, vars: Sequence[AST], **kwargs):
        self.labelled = labelled
        self.label = label
        self.vars = vars
        super().__init__(**kwargs)

    def translate_head(self, rule_id: int, disjunction_id: int, head: AST, body: Sequence[AST]):
        external_function = Function(
            location=loc,
            name="label",
            arguments=[self.label, Function(loc, "", self.vars, False)],
            external=True,
        )
        return literal(_TRACE_HEAD, [self.labelled, external_function], sign=Sign.NoSign)


class TraceRuleAnnotationRule(TraceAnnotation, FLit, XclingoRule):
    def __init__(self, trace_head: AST, **kwargs):
        super().__init__(
            labelled=Variable(loc, "Head"),
            label=trace_head.elements[0].terms[0],
            vars=trace_head.elements[0].terms[1:],
            disjunction_id=Variable(loc, "DisID"),
            head=Variable(loc, "Head"),
            **kwargs,
        )

    def translate_body(self, body: Sequence[AST]):
        yield self._reference_lit


class TraceAnnotationRule(TraceAnnotation, AutoSafeTheory, ModelBody, XclingoRule):
    def __init__(self, head: AST, **kwargs):
        super().__init__(
            labelled=head.elements[0].terms[0],
            label=head.elements[0].terms[1],
            vars=head.elements[0].terms[2:],
            head=head,
            **kwargs,
        )
