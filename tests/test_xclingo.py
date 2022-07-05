import pytest
from pathlib import PosixPath
from pickle import load
from typing import Tuple

from xclingo import XclingoControl
from xclingo.preprocessor import (
    ConstraintRelaxerPipeline,
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
    )
    xctl.extend_explainer("base", [], load_xclingo_extension("violated_constraints_minimize.lp"))
    xctl.extend_explainer("base", [], load_xclingo_extension("violated_constraints_show_trace.lp"))
    return xctl


class TestXclingo:
    """System test. From input to expected output."""

    cases = [
        ("4graphs", xctl_all()),
        ("constraint1", xctl_constraint()),
        ("count_aggregate", xctl_none()),
        ("diag", xctl_none()),
        ("diamond_with_mute", xctl_none()),
        ("disyunction", xctl_none()),
        ("dont_drive_drunk", xctl_none()),
        ("ignore_shows", xctl_all()),
        ("pool_and_choice", xctl_none()),
        ("pool_and_choice2", xctl_none()),
    ]

    @pytest.mark.parametrize("params", cases)
    def test_program(
        self,
        datadir: PosixPath,
        params: Tuple[str, XclingoControl],
    ):
        """Help function to test the otput of a test_case. It will take the name of the test and
        will try to retrieve two files from test_xclingo/ dir:
         - {test_case}.lp (the program to be tested)
         - {test_case}.txt (its expected output)

        Args:
            datadir (_type_): pytest_datadir plugin fixture
            test_case (str): name of the test case. It must match the one used in test_xclingo/ dir
            auto_tracing (str): xclingo auto_tracing mode.
        """
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

    # def test_cases_results(self, datadir):
    #     """This should test all the tests within the test_xclingo/ dir.

    #     It has to be updated every time a test is added
    #     """

    #     self.assert_test_case(
    #         datadir,
    #         "4graphs",
    #         self.xctl_all(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "constraint1",
    #         self.xctl_constraint(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "count_aggregate",
    #         self.xctl_none(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "diag",
    #         self.xctl_none(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "diamond_with_mute",
    #         self.xctl_none(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "disyunction",
    #         self.xctl_none(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "dont_drive_drunk",
    #         self.xctl_none(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "ignore_shows",
    #         self.xctl_all(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "pool_and_choice",
    #         self.xctl_none(),
    #     )
    #     self.assert_test_case(
    #         datadir,
    #         "pool_and_choice2",
    #         self.xctl_none(),
    #     )
