from clingo.symbol import Number
from ._utils import translate_show_all, translate_trace, translate_trace_all, translate_mute, \
    is_xclingo_label, is_xclingo_show_trace, is_choice_rule, is_label_rule, is_xclingo_mute, \
    is_constraint
from clingo import ast

class Preprocessor:
    def __init__(self):
        self._rule_count = 1
        self._last_trace_rule = None
        self._translation = ""
    
    def increment_rule_count(self):
        n = self._rule_count
        self._rule_count += 1
        return n

    @staticmethod
    def translate_annotations(program):
        return translate_trace_all(
            translate_show_all(
                translate_trace(
                    translate_mute(
                        program
                    )
                )
            )
        )

    def propagates(self, lit_list):
        for lit in lit_list:
            if lit.sign == ast.Sign.NoSign and lit.atom.ast_type == ast.ASTType.SymbolicAtom:
                yield lit        

    def sup_body(self, lit_list):
        loc = ast.Location(
                ast.Position("",0,0),
                ast.Position("",0,0),
            )
        for lit in lit_list:
            if lit.ast_type == ast.ASTType.Literal:
                if lit.atom.ast_type == ast.ASTType.SymbolicAtom:
                    yield ast.Literal(
                        loc,
                        lit.sign,
                        ast.SymbolicAtom(
                            ast.Function(
                                loc,
                                "_xclingo_model",
                                [lit.atom.symbol],
                                False,
                                )
                        )
                    )
                
                elif lit.atom.ast_type == ast.ASTType.BodyAggregate:
                    yield ast.Literal(
                        loc,
                        lit.sign,
                        ast.BodyAggregate(
                            loc,
                            left_guard=lit.atom.left_guard,
                            function=lit.atom.function,
                            elements=[
                                ast.BodyAggregateElement(
                                    terms=list(self.sup_body(e.terms)),
                                    condition=list(self.sup_body(e.condition)),
                                )
                                for e in lit.atom.elements
                            ],
                            right_guard=lit.atom.right_guard,
                        )
                    )
                
                else:
                    yield lit

            else:
                yield lit
    
    def sup_head(self, rule_id, rule_ast):
        loc = ast.Location(
                ast.Position("",0,0),
                ast.Position("",0,0),
            )
        head = ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        "_xclingo_sup",
                        [
                            ast.SymbolicTerm(loc, Number(rule_id)),
                            rule_ast.head.atom,
                            ast.Function( # tuple
                                loc,
                                '', 
                                list(self.propagates(rule_ast.body)),
                                False
                            )
                        ],
                        False,
                    ),
                )
            )
        return head

    def support_rule(self, rule_id, rule_ast):
        loc = ast.Location(
                ast.Position("",0,0),
                ast.Position("",0,0),
            )
        head = self.sup_head(rule_id, rule_ast)
        body = list(self.sup_body(rule_ast.body))

        return ast.Rule(loc, head, body)

    def fbody_head(self, rule_id, rule_ast):
        loc = ast.Location(
                ast.Position("",0,0),
                ast.Position("",0,0),
            )
        head = ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(
                    ast.Function(
                        loc,
                        "_xclingo_fbody",
                        [
                            ast.SymbolicTerm(loc, Number(rule_id)),
                            rule_ast.head.atom,
                            ast.Function( # tuple
                                loc,
                                '', 
                                list(self.propagates(rule_ast.body)),
                                False
                            )
                        ],
                        False,
                    ),
                )
            )
        return head

    def fbody_body(self, lit_list):
        loc = ast.Location(
                ast.Position("",0,0),
                ast.Position("",0,0),
            )
        for lit in lit_list:
            if lit.ast_type == ast.ASTType.Literal:
                if lit.atom.ast_type == ast.ASTType.SymbolicAtom:
                    if lit.sign == ast.Sign.NoSign:
                        yield ast.Literal(
                            loc,
                            lit.sign,
                            ast.SymbolicAtom(
                                ast.Function(
                                    loc,
                                    "_xclingo_f_atom",
                                    [lit.atom.symbol],
                                    False,
                                    )
                            )
                        )
                    else:
                        yield ast.Literal(
                            loc,
                            ast.Sign.Negation,
                            ast.SymbolicAtom(
                                ast.Function(
                                    loc,
                                    "_xclingo_model",
                                    [lit.atom.symbol],
                                    False,
                                    )
                            )
                        )
                
                elif lit.atom.ast_type == ast.ASTType.BodyAggregate:
                    yield ast.Literal(
                        loc,
                        lit.sign,
                        ast.BodyAggregate(
                            loc,
                            left_guard=lit.atom.left_guard,
                            function=lit.atom.function,
                            elements=[
                                ast.BodyAggregateElement(
                                    terms=list(self.fbody_body(e.terms)),
                                    condition=list(self.fbody_body(e.condition)),
                                )
                                for e in lit.atom.elements
                            ],
                            right_guard=lit.atom.right_guard,
                        )
                    )

                else:
                    yield lit
            else:
                yield lit

    def fbody_rule(self, rule_id, rule_ast):
        loc = ast.Location(
                ast.Position("",0,0),
                ast.Position("",0,0),
            )
        head = self.fbody_head(rule_id, rule_ast)
        body = list(self.fbody_body(rule_ast.body))
        return ast.Rule(loc, head, body)

    def label_rule(self, rule_id, label_rule_ast, rule_body):
        loc = ast.Location(
                ast.Position("",0,0),
                ast.Position("",0,0),
            )
        head_var = ast.Variable(loc, 'Head')
        head = ast.Literal(
            loc,
            label_rule_ast.head.sign,
            ast.SymbolicAtom(ast.Function(
                loc,
                label_rule_ast.head.atom.symbol.name,
                [
                    head_var,
                    label_rule_ast.head.atom.symbol.arguments[1]
                ],
                False,
            ))
        )
        body = [
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    '_xclingo_f',
                    [
                        ast.SymbolicTerm(loc, Number(rule_id)),
                        head_var,
                        ast.Function(
                            loc,
                            '',
                            list(self.propagates(rule_body)),
                            False,
                            ),
                    ],
                    False,
                ))
            )
        ]
        rule = ast.Rule(loc, head, body)
        return rule

    def label_atom(self, rule_ast):
        loc = ast.Location(
            ast.Position('', 0, 0),
            ast.Position('', 0, 0),
        )
        fatom = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(ast.Function(
                loc,
                '_xclingo_intree',
                [rule_ast.head.atom.symbol.arguments[0]],
                False,
            ))
        )
        body = [fatom] + list(self.sup_body(rule_ast.body))
        rule = ast.Rule(loc, rule_ast.head, body)
        return rule

    def show_trace(self, rule_ast):
        loc = ast.Location(
            ast.Position('', 0, 0),
            ast.Position('', 0, 0),
        )
        literal_head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(rule_ast.head.atom.symbol.arguments[0]),
        )
        rule = ast.Rule(loc, rule_ast.head, list(self.sup_body([literal_head] + list(rule_ast.body))))
        return rule

    def mute(self, rule_ast):
        loc = ast.Location(
            ast.Position('', 0, 0),
            ast.Position('', 0, 0),
        )
        literal_head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(rule_ast.head.atom.symbol.arguments[0]),
        )
        rule = ast.Rule(loc, rule_ast.head, list(self.sup_body([literal_head] + list(rule_ast.body))))
        return rule    

    def add_to_translation(self, a):
        self._translation+=f'{a}\n'

    def add_comment_to_translation(self, a):
        self._translation+=f'% {a}\n'

    def translate_rule(self, rule_ast):
        self.add_comment_to_translation(rule_ast)
        if rule_ast.ast_type == ast.ASTType.Rule and not is_constraint(rule_ast):
            if is_xclingo_label(rule_ast):
                if is_label_rule(rule_ast):
                    self._last_trace_rule = rule_ast
                    return
                self.add_to_translation(self.label_atom(rule_ast))
            elif is_xclingo_show_trace(rule_ast):
                self.add_to_translation(self.show_trace(rule_ast))
                pass
            elif is_xclingo_mute(rule_ast):
                self.add_to_translation(self.mute(rule_ast))
            else:
                rule_id = self.increment_rule_count()
                if is_choice_rule(rule_ast):
                    for cond_lit in rule_ast.head.elements:
                        false_rule = ast.Rule(
                            ast.Location(
                                ast.Position('',0,0),
                                ast.Position('',0,0),
                            ),
                            cond_lit.literal,
                            list(cond_lit.condition) + list(rule_ast.body),
                        )
                        self.add_to_translation(self.support_rule(rule_id, false_rule))
                        self.add_to_translation(self.fbody_rule(rule_id, false_rule))
                        if self._last_trace_rule is not None:
                            self.add_to_translation(self.label_rule(rule_id, self._last_trace_rule, false_rule.body))
                    if self._last_trace_rule is not None:
                        self._last_trace_rule = None
                else:  # Other cases
                    self.add_to_translation(self.support_rule(rule_id, rule_ast))
                    self.add_to_translation(self.fbody_rule(rule_id, rule_ast))
                    if self._last_trace_rule is not None:
                        self.add_to_translation(self.label_rule(rule_id, self._last_trace_rule, rule_ast.body))
                        self._last_trace_rule = None
    
    def translate_program(self, program, name=''):
        self._translation += '%'*8 + name + '%'*8 + '\n'
        ast.parse_string(
            Preprocessor.translate_annotations(program), 
            lambda ast: self.translate_rule(ast),
        )

    def get_translation(self):
        return self._translation
