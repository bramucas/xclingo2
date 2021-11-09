import re
from clingo import ast

def translate_trace(program):
    """
    Replaces the 'label_rule' magic comments in the given program for a version of the rules labelled with theory atoms.
    @param str program: the program that is intended to be modified.
    @return str:
    """
    for hit in re.findall("(%!trace_rule \{(\".*\")(?:,(.*))?\}[ ]*[\n ]*)", program):
        # 0: original match  1: label text  2: label parameters  3: head of the rule  4: body of the rule
        program = program.replace(
            hit[0],
            "{name}(id, @label({text}, ({parameters},) )).\n".format(
                text=hit[1], parameters=hit[2] if hit[2] else "",
                name="_xclingo_label"
            )
        )

    return program


def translate_trace_all(program):
    """
    Replaces the 'label_atoms' magic comments in the given program for label_atoms rule.
    @param str program: the program that is intended to be modified
    @return str:
    """
    for hit in re.findall("(%!trace \{(\".*\")(?:,(.*))?\} (\-?[_a-z][_a-zA-Z0-9]*(?:\((?:[\-\+a-zA-Z0-9 \(\)\,\_])+\))?)(?:[ ]*:[ ]*(.*))?\.)", program):
        # 0: original match 1: "label" 2:v1,v2  3: head  4: body.
        program = program.replace(
            hit[0],
            "{name}({head}, @label({text}, ({parameters},)) ){body}.".format(
                head=hit[3], 
                text=hit[1], 
                parameters=hit[2], 
                body=(" :- " + hit[4]) if hit[4] else "",
                name="_xclingo_label"
                )
        )

    return program


def translate_show_all(program):
    """
    Replaces 'explain' magic comments in the given program for a rule version of those magic comments.
    @param str program:
    @return:
    """
    for hit in re.findall("(%!show_trace ((\-)?([_a-z][_a-zA-Z0-9]*(?:\((?:[\-a-zA-Z0-9 \(\)\,\_])+\))?)(?:[ ]*:[ ]*(.*))?\.))", program):
        # 0: original match  1: rule  2: negative_sign  3: head of the rule  4: body of the rule
        program = program.replace(
            hit[0],
            "{name}({classic_negation}{head}){body}.".format(
                sign="" if not hit[2] else "n",
                name="_xclingo_show_trace",
                head=hit[3],
                classic_negation="" if not hit[2] else "-",
                body=" :- " + hit[4] if hit[4] else "")
        )

    return program

def translate_mute(program):
    """
    Replaces 'explain' magic comments in the given program for a rule version of those magic comments.
    @param str program:
    @return:
    """
    for hit in re.findall("(%!mute ((\-)?([_a-z][_a-zA-Z0-9]*(?:\((?:[\-a-zA-Z0-9 \(\)\,\_])+\))?)(?:[ ]*:[ ]*(.*))?\.))", program):
        # 0: original match  1: rule  2: negative_sign  3: head of the rule  4: body of the rule
        program = program.replace(
            hit[0],
            "{name}({classic_negation}{head}){body}.".format(
                sign="" if not hit[2] else "n",
                name="_xclingo_muted",
                head=hit[3],
                classic_negation="" if not hit[2] else "-",
                body=" :- " + hit[4] if hit[4] else "")
        )

    return program

def is_constraint(rule_ast):
    if rule_ast.ast_type == ast.ASTType.Rule:
        if hasattr(rule_ast.head, 'atom'):
            return  rule_ast.head.atom.ast_type == ast.ASTType.BooleanConstant \
                and rule_ast.head.atom == ast.BooleanConstant(0)
    return False
    

def is_xclingo_label(rule_ast):
    return rule_ast.head.ast_type == ast.ASTType.Literal \
        and rule_ast.head.atom.symbol.ast_type == ast.ASTType.Function \
        and rule_ast.head.atom.symbol.name == "_xclingo_label"

def is_xclingo_show_trace(rule_ast):
    return rule_ast.head.ast_type == ast.ASTType.Literal \
        and rule_ast.head.atom.symbol.ast_type == ast.ASTType.Function \
        and rule_ast.head.atom.symbol.name == "_xclingo_show_trace"

def is_xclingo_mute(rule_ast):
    return rule_ast.head.ast_type == ast.ASTType.Literal \
        and rule_ast.head.atom.symbol.ast_type == ast.ASTType.Function \
            and rule_ast.head.atom.symbol.name == "_xclingo_muted"

def is_label_rule(rule_ast):
    # Precondition: is_xclingo_label(rule_ast) == True
    return str(rule_ast.head.atom.symbol.arguments[0]) == "id"

def is_choice_rule(rule_ast):
    return rule_ast.head.ast_type == ast.ASTType.Aggregate \
        and hasattr(rule_ast.head, 'function') == False
