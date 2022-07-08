from typing import Callable, Sequence
from clingo import ast
from ._utils import (
    is_xclingo_label,
    is_xclingo_show_trace,
    is_choice_rule,
    is_label_rule,
    is_xclingo_mute,
    is_constraint,
    is_disyunctive_head,
    translate_trace,
    translate_trace_all,
    translate_show_all,
    translate_mute,
)

from ._transformers import (
    transformer_support_rule,
    transformer_fbody_rule,
    transformer_label_rule,
    transformer_label_atom,
    transformer_show_trace,
    transformer_mute,
    transformer_depends_rule,
    transformer_direct_cause,
    _xclingo_constraint_head,
    loc,
)


class Preprocessor:
    def __init__(self) -> None:
        self._translation = ""

    def reset(self) -> None:
        self._translation = ""

    def preprocess_rule(self, rule_ast: ast.AST) -> Sequence[ast.AST]:
        raise RuntimeError("This method is intended to be override")

    def _add_to_translation(self, rule_asts: Sequence[ast.AST]):
        """Adds the given rule to the internal translation.

        Args:
            rule_ast (ast.AST): the rule to add to the translation.
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
        ast.parse_string(
            program,
            lambda ast: self._add_to_translation(self.preprocess_rule(ast)),
        )
        return self._translation


class XClingoAnnotationPreprocessor(Preprocessor):
    def __init__(self) -> None:
        super().__init__()

    def reset(self) -> None:
        super().reset()

    def preprocess_rule(self, rule_ast: ast.AST) -> None:
        if (
            rule_ast.ast_type == ast.ASTType.Rule
            and rule_ast.head.ast_type == ast.ASTType.TheoryAtom
        ):
            name = rule_ast.head.term.name
            if name == "trace_rule":
                rule_ast = translate_trace(rule_ast)
            elif name == "trace":
                rule_ast = translate_trace_all(rule_ast)
            elif name == "show_trace":
                rule_ast = translate_show_all(rule_ast)
            elif name == "mute":
                rule_ast = translate_mute(rule_ast)
        yield rule_ast

    def process_program(self, program: str):
        return super().process_program(program.replace("%!", "&"))


class ConstraintRelaxer(Preprocessor):
    """Relaxes the constraints in the program. This is, traced constraints become rules with special
    heads.

    Created heads have the form: xclingo_violated_constraint(<number>). This number ID is
    independent from the number of rules in the program.
    """

    def __init__(self, preserve_labels=False):
        super().__init__()
        self._constraint_count = 1
        self._lits = []
        self.there_is_a_label = False
        self.preserve_labels = preserve_labels

    def reset(self):
        super().reset()
        self._constraint_count = 1
        self._lits = []
        self.there_is_a_label = False

    def _increment_constraint_count(self):
        """Returns the current ID for constraints and increment the internal counter."""
        n = self._constraint_count
        self._constraint_count += 1
        return n

    def _relaxed_constraint(self, rule_id: int, rule_ast: ast.AST):
        return ast.Rule(
            location=loc, head=_xclingo_constraint_head(rule_id, rule_ast.body), body=rule_ast.body
        )

    def preprocess_rule(self, rule_ast: ast.AST):
        """Preprocess the given rule and adds the result to the translation.

        Labelled constraints are transformed into their relaxed form. The rest of the program is
        unchanged.

        Args:
            rule_ast (ast.AST): rule to be preprocessed and added to the translation.
        """
        # if there is a label, self.there_is_a_label is set to True but it's not used
        if is_xclingo_label(rule_ast):
            self.there_is_a_label = True
            if self.preserve_labels:
                yield rule_ast
        else:
            if rule_ast.ast_type == ast.ASTType.Rule:
                rule_id = self._increment_constraint_count()
            #  if there is a constraint and self.there_is_a_label is True, we put a head and add it to the translation
            if is_constraint(rule_ast) and self.there_is_a_label is True:
                rule_ast = self._relaxed_constraint(rule_id, rule_ast)
            self.there_is_a_label = False
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

    def reset(self):
        super().reset()
        self._rule_count = 1
        self._last_trace_rule = None

    def _increment_rule_count(self):
        """Returns the current ID for rules and increment the internal counter."""
        n = self._rule_count
        self._rule_count += 1
        return n

    def translate_rules(self, rule_id: int, disyunction_id: int, rule_ast: ast.ASTType.Rule):
        fbody_rule = transformer_fbody_rule(rule_id, disyunction_id, rule_ast)
        yield fbody_rule
        for dep_rule in transformer_direct_cause(fbody_rule.head, fbody_rule.body):
            yield dep_rule
        sup_rule = transformer_support_rule(rule_id, disyunction_id, rule_ast)
        yield sup_rule
        for dep_rule in transformer_depends_rule(sup_rule.head, sup_rule.body):
            yield dep_rule

    def preprocess_rule(self, rule_ast: ast.ASTType.Rule):
        """Translates a given rule into its xclingo translation and adds it to the translation.
        Before every addition, a comment containing the original rule is also added.

        Not traced constraints will be ignored.

        Args:
            rule_ast (ast.ASTType.Rule): rule to be translated.
        """
        # Ignore #shows
        if rule_ast.ast_type == ast.ASTType.ShowSignature:
            return
        # TODO: what to do with externals?
        # TODO: which other things
        self._add_comment_to_translation(rule_ast)
        if rule_ast.ast_type != ast.ASTType.Rule:
            yield rule_ast  # Things that are not rules are just passed
        else:

            if is_xclingo_label(rule_ast):
                if is_label_rule(rule_ast):
                    self._last_trace_rule = rule_ast
                    return
                else:  # if it is label atom
                    yield transformer_label_atom(rule_ast)

            elif is_xclingo_show_trace(rule_ast):
                yield transformer_show_trace(rule_ast)

            elif is_xclingo_mute(rule_ast):
                yield transformer_mute(rule_ast)

            else:
                rule_id = self._increment_rule_count()

                if is_choice_rule(rule_ast):
                    for cond_lit in rule_ast.head.elements:
                        rule_ast = ast.Rule(
                            loc, cond_lit.literal, list(cond_lit.condition) + list(rule_ast.body)
                        )
                        for r in self.translate_rules(rule_id, 0, rule_ast):
                            yield r

                elif is_disyunctive_head(rule_ast):
                    disjunction_id = 0
                    for cond_lit in rule_ast.head.elements:
                        rule_ast = ast.Rule(
                            loc, cond_lit.literal, list(cond_lit.condition) + list(rule_ast.body)
                        )
                        for r in self.translate_rules(rule_id, disjunction_id, rule_ast):
                            yield r
                        disjunction_id += 1

                else:
                    # Fake relaxed constraint rule
                    if is_constraint(rule_ast):
                        if self._last_trace_rule is None:
                            return
                        else:
                            rule_ast = ast.Rule(
                                loc, _xclingo_constraint_head(rule_id, rule_ast.body), rule_ast.body
                            )
                    for r in self.translate_rules(rule_id, 0, rule_ast):
                        yield r

                if self._last_trace_rule is not None:
                    yield transformer_label_rule(rule_id, self._last_trace_rule, rule_ast.body)
                    self._last_trace_rule = None
