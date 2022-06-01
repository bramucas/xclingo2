from clingo.symbol import Number
import pytest
import clingo.ast as ast
from clingo import Number, String
from xclingo.preprocessor import Preprocessor

class TestPreprocessor:

    @pytest.fixture(scope='class')
    def custom_body(self):
        loc = ast.Location(ast.Position("",0,0), ast.Position("",0,0))
        custom_body = [
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "person",[ast.Variable(loc, 'P')],False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "hola",[],False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.Negation,
                ast.SymbolicAtom(ast.Function(loc, "nothola",[],False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.Comparison(
                    ast.ComparisonOperator.Equal,
                    ast.SymbolicTerm(loc, Number(1)),
                    ast.SymbolicTerm(loc, Number(1)),
                )
            )
        ]
        return custom_body

    @pytest.fixture(scope='class')
    def expected_sup_body(self):
        loc = ast.Location(ast.Position("",0,0), ast.Position("",0,0))
        expected_body = [
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "_xclingo_model", [ast.Function(loc, "person",[ast.Variable(loc, 'P')],False)], False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "_xclingo_model", [ast.Function(loc, "hola",[],False)], False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.Negation,
                ast.SymbolicAtom(ast.Function(loc, "_xclingo_model", [ast.Function(loc, "nothola",[],False)], False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.Comparison(
                    ast.ComparisonOperator.Equal,
                    ast.SymbolicTerm(loc, Number(1)),
                    ast.SymbolicTerm(loc, Number(1)),
                )
            )
        ]
        return expected_body

    @pytest.fixture(scope='class')
    def expected_fbody_body(self):
        loc = ast.Location(ast.Position("",0,0), ast.Position("",0,0))
        expected_body = [
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "_xclingo_f_atom", [ast.Function(loc, "person",[ast.Variable(loc, 'P')],False)], False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "_xclingo_f_atom", [ast.Function(loc, "hola",[],False)], False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.Negation,
                ast.SymbolicAtom(ast.Function(loc, "_xclingo_model", [ast.Function(loc, "nothola",[],False)], False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.Comparison(
                    ast.ComparisonOperator.Equal,
                    ast.SymbolicTerm(loc, Number(1)),
                    ast.SymbolicTerm(loc, Number(1)),
                )
            )
        ]
        return expected_body

    @pytest.fixture(scope='class')
    def expected_propagates(self):
        loc = ast.Location(ast.Position("",0,0), ast.Position("",0,0))
        expected_propagates = [
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "person",[ast.Variable(loc, 'P')],False)),
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(loc, "hola",[],False)),
            )
        ]
        return expected_propagates

    @pytest.fixture(scope='class')
    def custom_rule(self, custom_body):
        loc = ast.Location(ast.Position('', 0, 0), ast.Position('', 0, 0))
        lit = ast.Literal(
            loc, 
            ast.Sign.NoSign, 
            ast.SymbolicAtom(ast.Function(loc, 'b', [], False))
            )
        custom_rule = ast.Rule(loc, lit, custom_body)
        return custom_rule

    @pytest.fixture(scope='class')
    def expected_support_rule(self, expected_sup_body):
        rule_id=32
        loc = ast.Location(
            ast.Position("", 0, 0), ast.Position("", 0, 0)
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(ast.Function(
                loc,
                '_xclingo_sup',
                [
                    ast.SymbolicTerm(loc, Number(rule_id)),
                    ast.SymbolicAtom(ast.Function(loc, 'b', [], False)),
                    ast.Function(
                        loc,
                        '',
                        [
                            ast.Literal(
                                loc,
                                ast.Sign.NoSign,
                                ast.SymbolicAtom(ast.Function(loc, "person",[ast.Variable(loc, 'P')],False)),
                            ),
                            ast.Literal(
                                loc,
                                ast.Sign.NoSign,
                                ast.SymbolicAtom(ast.Function(loc, "hola",[],False)),
                            )
                        ],
                        False,
                    )
                ],
                False,
            ))
        )
        expected_sup_rule = ast.Rule(loc, head, expected_sup_body)
        return rule_id, expected_sup_rule

    @pytest.fixture(scope='class')
    def expected_fbody_rule(self, expected_fbody_body):
        rule_id=32
        loc = ast.Location(
            ast.Position("", 0, 0), ast.Position("", 0, 0)
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(ast.Function(
                loc,
                '_xclingo_fbody',
                [
                    ast.SymbolicTerm(loc, Number(rule_id)),
                    ast.SymbolicAtom(ast.Function(loc, 'b', [], False)),
                    ast.Function(
                        loc,
                        '',
                        [
                            ast.Literal(
                                loc,
                                ast.Sign.NoSign,
                                ast.SymbolicAtom(ast.Function(loc, "person",[ast.Variable(loc, 'P')],False)),
                            ),
                            ast.Literal(
                                loc,
                                ast.Sign.NoSign,
                                ast.SymbolicAtom(ast.Function(loc, "hola",[],False)),
                            )
                        ],
                        False,
                    )
                ],
                False,
            ))
        )
        expected_fbody_rule = ast.Rule(loc, head, expected_fbody_body)
        return rule_id, expected_fbody_rule

    @pytest.fixture(scope='class')
    def custom_label_rule(self):
        loc = ast.Location(
            ast.Position("", 0, 0), ast.Position("", 0, 0)
        )
        return ast.Rule(
            loc,
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    '_xclingo_label',
                    [
                        ast.SymbolicAtom(ast.Function(
                            loc,
                            'id',
                            [],
                            False,
                        )),
                        ast.SymbolicAtom(ast.Function(
                            loc,
                            'label',
                            [
                                ast.SymbolicTerm(loc, String("persona %")),
                                ast.Function(
                                    loc,
                                    '',
                                    [ast.Variable(loc, 'P')],
                                    False,
                                )
                            ],
                            True,
                        )),
                    ],
                    False,
                ))
            ),
            [],
        )

    @pytest.fixture(scope='class')
    def expected_label_rule(self):
        rule_id = 32
        loc = ast.Location(
            ast.Position("", 0, 0), ast.Position("", 0, 0)
        )
        head_var = ast.Variable(loc, 'Head')
        head = ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    '_xclingo_label',
                    [
                        head_var,
                        ast.SymbolicAtom(ast.Function(
                            loc,
                            'label',
                            [
                                ast.SymbolicTerm(loc, String("persona %")),
                                ast.Function(
                                    loc,
                                    '',
                                    [ast.Variable(loc, 'P')],
                                    False,
                                )
                            ],
                            True,
                        )),
                    ],
                    False,
                ))
            ),
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
                                [
                                    ast.Literal(
                                        loc,
                                        ast.Sign.NoSign,
                                        ast.SymbolicAtom(ast.Function(loc, "person",[ast.Variable(loc, 'P')],False)),
                                    ),
                                    ast.Literal(
                                        loc,
                                        ast.Sign.NoSign,
                                        ast.SymbolicAtom(ast.Function(loc, "hola",[],False)),
                                    )
                                ],
                                False,
                            )

                        ],
                        False,
                    ))
                )
            ],
        rule = ast.Rule(
            loc,
            head[0],
            body[0],
        )
        return rule_id, rule

    @pytest.fixture(scope='class')
    def custom_label_atom(self):
        loc = ast.Location(
            ast.Position("", 0, 0), ast.Position("", 0, 0)
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(ast.Function(
                loc,
                '_xclingo_label',
                [
                    ast.SymbolicAtom(ast.Function(
                        loc,
                        'alcohol',
                        [ast.Variable(loc, 'P'), ast.Variable(loc, 'A')],
                        False,
                    )),
                    ast.SymbolicAtom(ast.Function(
                        loc,
                        'label',
                        [
                            ast.SymbolicTerm(loc, String("% alcohol's level is %")),
                            ast.Function(
                                loc,
                                '',
                                [ast.Variable(loc, 'P'), ast.Variable(loc, 'A')],
                                False,
                            )
                        ],
                        True,
                    )),
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
                    'person',
                    [ast.Variable(loc, 'P')],
                    False,
                ))
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.Comparison(
                    ast.ComparisonOperator.GreaterThan,
                    ast.Variable(loc, 'A'),
                    ast.SymbolicTerm(loc, Number(30)),
                )
            ),
            ast.Literal(
                loc,
                ast.Sign.Negation,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    'inprison',
                    [ast.Variable(loc, 'P')],
                    False,
                ))
            )
        ]
        rule = ast.Rule(loc, head, body)
        return rule

    @pytest.fixture(scope='class')
    def expected_label_atom(self):
        loc = ast.Location(
            ast.Position("", 0, 0), ast.Position("", 0, 0)
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(ast.Function(
                loc,
                '_xclingo_label',
                [
                    ast.SymbolicAtom(ast.Function(
                        loc,
                        'alcohol',
                        [ast.Variable(loc, 'P'), ast.Variable(loc, 'A')],
                        False,
                    )),
                    ast.SymbolicAtom(ast.Function(
                        loc,
                        'label',
                        [
                            ast.SymbolicTerm(loc, String("% alcohol's level is %")),
                            ast.Function(
                                loc,
                                '',
                                [ast.Variable(loc, 'P'), ast.Variable(loc, 'A')],
                                False,
                            )
                        ],
                        True,
                    )),
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
                    '_xclingo_intree',
                    [
                        ast.SymbolicAtom(ast.Function(
                            loc,
                            'alcohol',
                            [ast.Variable(loc, 'P'), ast.Variable(loc, 'A')],
                            False,
                        )),
                    ],
                    False,
                ))
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    '_xclingo_model',
                    [
                        ast.Function(
                            loc,
                            'person',
                            [ast.Variable(loc, 'P')],
                            False,
                        )
                    ],
                    False,
                ))
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.Comparison(
                    ast.ComparisonOperator.GreaterThan,
                    ast.Variable(loc, 'A'),
                    ast.SymbolicTerm(loc, Number(30)),
                )
            ),
            ast.Literal(
                loc,
                ast.Sign.Negation,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    '_xclingo_model',
                    [
                        ast.Function(
                            loc,
                            'inprison',
                            [ast.Variable(loc, 'P')],
                            False,
                        )
                    ],
                    False
                )),
            )
        ]
        rule = ast.Rule(loc, head, body)
        return rule

    @pytest.fixture(scope='class')
    def custom_show_trace(self):
        loc = ast.Location(
            ast.Position('', 0, 0),
            ast.Position('', 0, 0),
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(ast.Function(
                loc,
                '_xclingo_show_trace',
                [
                    ast.Function(
                        loc,
                        'sentence',
                        [ast.Variable(loc, 'P'), ast.Variable(loc, 'S')],
                        False,
                    ),
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
                    'person',
                    [ast.Variable(loc, 'P')],
                    False,
                ))
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.Comparison(
                    ast.ComparisonOperator.Equal,
                    ast.Variable(loc, 'P'),
                    ast.SymbolicAtom(ast.Function(
                        loc,
                        'gabriel',
                        [],
                        False,
                    )),
                )
            ),
            ast.Literal(
                loc,
                ast.Sign.Negation,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    'inprison',
                    [ast.Variable(loc, 'P')],
                    False,
                ))
            )
        ]
        rule = ast.Rule(loc, head, body)
        return rule

    @pytest.fixture(scope='class')
    def expected_show_trace(self):
        loc = ast.Location(
            ast.Position('', 0, 0),
            ast.Position('', 0, 0),
        )
        head = ast.Literal(
            loc,
            ast.Sign.NoSign,
            ast.SymbolicAtom(ast.Function(
                loc,
                '_xclingo_show_trace',
                [
                    ast.Function(
                        loc,
                        'sentence',
                        [ast.Variable(loc, 'P'), ast.Variable(loc, 'S')],
                        False,
                    ),
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
                    '_xclingo_model',
                    [
                        ast.Function(
                            loc,
                            'sentence',
                            [ast.Variable(loc, 'P'), ast.Variable(loc, 'S')],
                            False,
                        ),
                    ],
                    False,
                ))
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    '_xclingo_model',
                    [
                        ast.Function(
                            loc,
                            'person',
                            [ast.Variable(loc, 'P')],
                            False,
                        ),
                    ],
                    False,
                ))
            ),
            ast.Literal(
                loc,
                ast.Sign.NoSign,
                ast.Comparison(
                    ast.ComparisonOperator.Equal,
                    ast.Variable(loc, 'P'),
                    ast.SymbolicAtom(ast.Function(
                        loc,
                        'gabriel',
                        [],
                        False,
                    )),
                )
            ),
            ast.Literal(
                loc,
                ast.Sign.Negation,
                ast.SymbolicAtom(ast.Function(
                    loc,
                    '_xclingo_model',
                    [
                        ast.Function(
                            loc,
                            'inprison',
                            [ast.Variable(loc, 'P')],
                            False,
                        )
                    ],
                    False,
                ))
            )
        ]
        rule = ast.Rule(loc, head, body)
        return rule
        

    def test_propagates(self, custom_body, expected_propagates):
        preprocessor = Preprocessor()
        assert expected_propagates == list(preprocessor.propagates(custom_body))

    def test_sup_body(self, custom_body, expected_sup_body):
        preprocessor = Preprocessor()
        assert expected_sup_body == list(preprocessor.sup_body(custom_body))

    def test_sup_rule(self, custom_rule, expected_support_rule):
        rule_id, expected = expected_support_rule
        preprocessor = Preprocessor()
        support_rule = preprocessor.support_rule(rule_id, custom_rule)
        assert expected == support_rule

    def test_fbody_body(self, custom_body, expected_fbody_body):
        preprocessor = Preprocessor()
        body = list(preprocessor.fbody_body(custom_body))
        assert expected_fbody_body == body

    def test_fbody_rule(self, custom_rule, expected_fbody_rule):
        preprocessor = Preprocessor()
        rule_id, expected = expected_fbody_rule
        rule = preprocessor.fbody_rule(rule_id, custom_rule)
        assert expected == rule

    def test_label_rule(self, custom_label_rule, expected_label_rule, custom_body):
        preprocessor = Preprocessor()
        rule_id, expected = expected_label_rule
        rule = preprocessor.label_rule(rule_id, custom_label_rule, custom_body)
        assert expected == rule

    def test_label_atom(self, custom_label_atom, expected_label_atom):
        preprocessor = Preprocessor()
        rule = preprocessor.label_atom(custom_label_atom)
        assert expected_label_atom == rule

    def test_show_trace(self, custom_show_trace, expected_show_trace):
        preprocessor = Preprocessor()
        rule = preprocessor.show_trace(custom_show_trace)
        assert expected_show_trace == rule
