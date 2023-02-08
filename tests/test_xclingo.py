import pytest
from pathlib import PosixPath
from pickle import load
from typing import Tuple

from xclingo import XclingoControl
from xclingo.preprocessor import (
    ConstraintRelaxerPipeline,
    ConstraintExplainingPipeline,
)
from xclingo.extensions import load_xclingo_extension


def xctl_all():
    xctl = XclingoControl(
        ["0"],
        n_explanations="0",
    )
    xctl.extend_explainer("base", [], load_xclingo_extension("autotrace_all.lp"))
    return xctl


def xctl_none():
    xctl = XclingoControl(
        ["0"],
        n_explanations="0",
    )
    return xctl


def xctl_constraint():
    xctl = XclingoControl(
        ["0"],
        n_explanations="0",
        solving_preprocessor_pipeline=ConstraintRelaxerPipeline(),
        explaining_preprocessor_pipeline=ConstraintExplainingPipeline(),
    )
    xctl.extend_explainer("base", [], load_xclingo_extension("violated_constraints_minimize.lp"))
    xctl.extend_explainer("base", [], load_xclingo_extension("violated_constraints_show_trace.lp"))
    return xctl


class TestXclingo:
    """System test. From input to expected output."""

    cases = [
        ("_annotation_operator", xctl_none()),  # 0
        ("_cond_lit", xctl_all()),
        ("_ignore_non_labelled_constraints", xctl_all()),
        ("_mute_body", xctl_none()),
        ("_showtrace_1", xctl_none()),
        ("_showtrace_2", xctl_none()),  # 5
        ("_showtrace_3", xctl_none()),
        ("_trace_1", xctl_none()),
        ("_trace_2", xctl_none()),
        ("_trace_3", xctl_none()),
        ("4graphs", xctl_all()),  # 10
        ("constraint1", xctl_constraint()),
        ("count_aggregate", xctl_none()),
        ("diag", xctl_none()),
        ("diamond_with_mute", xctl_none()),
        ("disyunction", xctl_none()),  # 15
        ("dont_drive_drunk", xctl_none()),
        ("happy", xctl_none()),
        ("ignore_shows", xctl_all()),
        ("obligations_gentle_killer", xctl_none()),
        ("pool_and_choice", xctl_none()),  # 20
        ("pool_and_choice2", xctl_none()),
        ("single_strongneg", xctl_none()),
        ("unbalanced_table", xctl_all()),  # 23
    ]

    @pytest.mark.parametrize("params", cases)
    def test_program(
        self,
        datadir: PosixPath,
        params: Tuple[str, XclingoControl],
    ):

        test_case, xclingo_control = params
        print(f"!! Testing {test_case}:", end="  ")

        xclingo_control.add("base", [], (datadir / f"{test_case}_test.lp").read_text())
        xclingo_control.ground([("base", [])])
        print("GROUNDED", end="  ")

        buf = []
        for xmodel in xclingo_control.solve():
            for graph_model in xmodel.explain_model():
                buf.append(frozenset(str(s) for s in graph_model.symbols(shown=True)))
        result = frozenset(buf)
        print("SOLVED", end="  ")

        expected = load((datadir / f"{test_case}_res.pickle").open("rb"))
        assert expected == result
        print("CORRECT")
