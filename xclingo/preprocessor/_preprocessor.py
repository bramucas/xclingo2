from typing import Sequence
from clingo.ast import (
    AST,
    ASTType,
)
from clingo.ast import parse_string
from .xclingo_ast import (
    is_choice_rule,
    is_constraint,
    is_disyunctive_head,
    is_theory_head,
)

from ._translator import (
    SupportTranslator,
    AnnotationTranslator,
    RelaxedConstraintTranslator,
    AnnotationNames,
)


def xclingo_annotation(rule_ast):
    if rule_ast.ast_type == ASTType.Rule and rule_ast.head.ast_type == ASTType.TheoryAtom:
        if rule_ast.head.term.name in AnnotationNames.all():
            return rule_ast.head.term.name
    return None


class Preprocessor:
    def __init__(self) -> None:
        self._translation = ""

    def reset(self) -> None:
        self._translation = ""

    def preprocess_rule(self, rule_ast: AST) -> Sequence[AST]:
        raise RuntimeError("This method is intended to be override")

    def _add_to_translation(self, rule_asts: Sequence[AST]):
        """Adds the given rule to the internal translation.

        Args:
            rule_ast (AST): the rule to add to the translation.
        """
        for ra in rule_asts:
            self._translation += f"{ra}\n"

    def _add_comment_to_translation(self, comment: str):
        """Adds a comment to the internal translation.

        Args:
            comment (str): the comment to add to the translation.
        """
        self._translation += f"% {comment}\n"

    def process_program(self, program: str):
        """Translates a given program into its xclingo translation. The translation starts with a comment containing the program name.

        Args:
            program (str): program to be translated.
            name (str, optional): Defaults to "".
        """
        self._translation = ""
        parse_string(
            program,
            lambda ast: self._add_to_translation(self.preprocess_rule(ast)),
        )
        return self._translation


class XClingoAnnotationPreprocessor(Preprocessor):
    def __init__(self) -> None:
        super().__init__()

    def reset(self) -> None:
        super().reset()

    def preprocess_rule(self, rule_ast: AST) -> None:
        yield rule_ast

    def process_program(self, program: str):
        return super().process_program(program.replace("%!", "&"))


class ConstraintRelaxer(Preprocessor):
    """Relaxes the constraints in the program. This is, traced constraints become rules with special
    heads.

    Created heads have the form: xclingo_violated_constraint(<number>). This number ID is
    independent from the number of rules in the program.
    """

    def __init__(self, keep_annotations: bool = False):
        super().__init__()
        self._constraint_count = 1
        self.there_is_a_label = False
        self._keep_annotations = keep_annotations
        self._relaxed_constraint_translator = RelaxedConstraintTranslator()

    def reset(self):
        super().reset()
        self._constraint_count = 1
        self.there_is_a_label = False

    def _increment_constraint_count(self):
        """Returns the current ID for constraints and increment the internal counter."""
        n = self._constraint_count
        self._constraint_count += 1
        return n

    def preprocess_rule(self, rule_ast: AST):
        """Preprocess the given rule and adds the result to the translation.

        Labelled constraints are transformed into their relaxed form. The rest of the program is
        unchanged.

        Args:
            rule_ast (AST): rule to be preprocessed and added to the translation.
        """
        self._add_comment_to_translation(rule_ast)
        # Ignore #shows
        if rule_ast.ast_type == ASTType.ShowSignature:
            return

        if rule_ast.ast_type != ASTType.Rule:
            yield rule_ast  # Things that are not rules are just passed
        else:
            annotation_name = xclingo_annotation(rule_ast)

            if annotation_name is None:  # Rules
                rule_id = self._increment_constraint_count()
                if is_constraint(rule_ast) and self.there_is_a_label is True:
                    for translated_constraint in self._relaxed_constraint_translator.translate(
                        rule_id, rule_ast
                    ):
                        yield translated_constraint
                else:
                    yield rule_ast
                self.there_is_a_label = False

            else:  # Annotations
                if annotation_name == "trace_rule":
                    self.there_is_a_label = True
                if self._keep_annotations:
                    yield rule_ast


class XClingoPreprocessor(Preprocessor):
    """Translates a given program into the xclingo format.

    For every original rule ID is given and the following happens:
    - the original rule is added as a comment in the translation.
    - a support rule (_xclingo_sup/3) is added to the translation. The body of this rule is the positive
    part of the original rule, written in terms of _xclngo_model/1 facts.
    - a fired_body rule (_xclingo_fbody/3) is added to the translation. The body of this rule is the
    positive part of the orignal rule, written in terms of _xclingo_f_atom/1 facts.
    - if the rule is traced, a label rule (_xclingo_label/2) is added to the translation. The body of
    this rule directly depends of the corresponding _xclingo_f/3 fact of the traced rule.
    - traced constraints are also translated into their xclingo forms. Not traced constraints are
    ignored.

    xClingo anotations are translated into its xclingo forms:
    - %!show_trace: translated into a rule with head _xclingo_show_trace/1.
    - %!trace: translated into a rule with head _xclingo_trace/2.
    """

    def __init__(self):
        super().__init__()
        self._rule_count = 1
        self._last_trace_rule = None
        self._annotation_translator = AnnotationTranslator()
        self._support_translator = SupportTranslator()

    def reset(self):
        super().reset()
        self._rule_count = 1
        self._last_trace_rule = None

    def _increment_rule_count(self):
        """Returns the current ID for rules and increment the internal counter."""
        n = self._rule_count
        self._rule_count += 1
        return n

    def translate_annotation(self, annotation_name: str, rule_ast: AST):
        for translated_annotation in self._annotation_translator.translate(
            annotation_name,
            rule_ast,
            self._rule_count,
        ):
            yield translated_annotation

    def translate_rule(
        self,
        rule_id: int,
        disjunction_id: int,
        original_head: AST,
        original_body: Sequence[AST],
    ):
        for translated_rule in self._support_translator.translate(
            rule_id, disjunction_id, original_head, original_body, self._last_trace_rule
        ):
            yield translated_rule

    def preprocess_rule(self, rule_ast: ASTType.Rule):
        """Translates a given rule into its xclingo translation and adds it to the translation.
        Before every addition, a comment containing the original rule is also added.

        Not traced constraints will be ignored.

        Args:
            rule_ast (ASTType.Rule): rule to be translated.
        """
        # Ignore #shows
        if rule_ast.ast_type == ASTType.ShowSignature:
            return
        # TODO: what to do with externals?
        # TODO: which other things
        self._add_comment_to_translation(rule_ast)
        if rule_ast.ast_type != ASTType.Rule:
            yield rule_ast  # Things that are not rules are just passed
        else:
            # Checks if it is an xclingo annotation
            annotation_name = xclingo_annotation(rule_ast)
            if annotation_name is not None:
                if annotation_name == "trace_rule":
                    self._last_trace_rule = rule_ast
                else:
                    for translated_annotation in self.translate_annotation(
                        annotation_name,
                        rule_ast,
                    ):
                        yield translated_annotation
            else:
                rule_id = self._increment_rule_count()

                if is_theory_head(rule_ast):  # Is not an xclingo theory atom
                    yield rule_ast
                    return

                if is_choice_rule(rule_ast):
                    for cond_lit in rule_ast.head.elements:

                        for r in self.translate_rule(
                            rule_id,
                            0,
                            cond_lit.literal,
                            list(cond_lit.condition) + list(rule_ast.body),
                        ):
                            yield r

                elif is_disyunctive_head(rule_ast):
                    disjunction_id = 0
                    for cond_lit in rule_ast.head.elements:
                        for r in self.translate_rule(
                            rule_id,
                            disjunction_id,
                            cond_lit.literal,
                            list(cond_lit.condition) + list(rule_ast.body),
                        ):
                            yield r
                        disjunction_id += 1
                elif not is_constraint(rule_ast):
                    for r in self.translate_rule(rule_id, 0, rule_ast.head, rule_ast.body):
                        yield r

                self._last_trace_rule = None
