import pytest

from xclingo import XclingoControl
from xclingo.preprocessor import (
    ConstraintRelaxerPipeline,
)
from xclingo.extensions import load_xclingo_extension


class TestXclingo:
    """System test. From input to expected output."""

    def xctl_all(self):
        xctl = XclingoControl(
            ["0"],
            n_explanations="0",
        )
        xctl.add_to_explainer("base", [], load_xclingo_extension("autotrace_all.lp"))
        return xctl

    def xctl_none(self):
        xctl = XclingoControl(
            ["0"],
            n_explanations="0",
        )
        return xctl

    def xctl_constraint(self):
        xctl = XclingoControl(
            ["0"],
            n_explanations="0",
            solving_preprocessor_pipeline=ConstraintRelaxerPipeline(),
        )
        xctl.add_to_explainer(
            "base", [], load_xclingo_extension("violated_constraints_minimize.lp")
        )
        xctl.add_to_explainer(
            "base", [], load_xclingo_extension("violated_constraints_show_trace.lp")
        )
        return xctl

    def assert_test_case(
        self,
        datadir,
        test_case: str,
        xclingo_control: XclingoControl,
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
        xclingo_control.add("base", [], (datadir / f"{test_case}_test.lp").read_text())
        xclingo_control.ground([("base", [])])

        result = xclingo_control._default_output()
        expected = (datadir / f"{test_case}_res.txt").read_text()
        assert expected == result

    def test_cases_results(self, datadir):
        """This should test all the tests within the test_xclingo/ dir.

        It has to be updated every time a test is added
        """

        self.assert_test_case(
            datadir,
            "4graphs",
            self.xctl_all(),
        )
        self.assert_test_case(
            datadir,
            "constraint1",
            self.xctl_constraint(),
        )
        self.assert_test_case(
            datadir,
            "count_aggregate",
            self.xctl_none(),
        )
        self.assert_test_case(
            datadir,
            "diamond_with_mute",
            self.xctl_none(),
        )
        self.assert_test_case(
            datadir,
            "dont_drive_drunk",
            self.xctl_none(),
        )
        self.assert_test_case(
            datadir,
            "ignore_shows",
            self.xctl_all(),
        )
        self.assert_test_case(
            datadir,
            "pool_and_choice",
            self.xctl_none(),
        )
        self.assert_test_case(
            datadir,
            "pool_and_choice2",
            self.xctl_none(),
        )
