import pytest
from sklearn.covariance import graphical_lasso

from xclingo import XclingoControl
from xclingo.preprocessor import (
    DefaultExplainingPipeline,
    ConstraintRelaxerPipeline,
    PreprocessorPipeline,
)
from xclingo.extensions import ExtensionLoader


class TestXclingo:
    """System test. From input to expected output."""

    def assert_test_case(
        self,
        datadir,
        test_case,
        pre_solving_pipeline,
        pre_explaining_pipeline,
        lp_extensions=[],
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
        xcontrol = XclingoControl(
            n_solutions="0",
            n_explanations="0",
            pre_solving_pipeline=pre_solving_pipeline,
            pre_explainer_pipeline=pre_explaining_pipeline,
            lp_extensions=lp_extensions,
        )

        xcontrol.add("base", [], (datadir / f"{test_case}_test.lp").read_text())
        xcontrol.ground()

        result = xcontrol._default_output()
        expected = (datadir / f"{test_case}_res.txt").read_text()
        assert expected == result

    def test_cases_results(self, datadir):
        """This should test all the tests within the test_xclingo/ dir.

        It has to be updated every time a test is added
        """
        # Prepare extensions
        auto_trace = ExtensionLoader()
        auto_trace.loadLPExtension("autotrace_all.lp")

        constraints = ExtensionLoader()
        constraints.loadLPExtension("violated_constraints_show_trace.lp")
        constraints.loadLPExtension("violated_constraints_minimize.lp")

        self.assert_test_case(
            datadir,
            "4graphs",
            PreprocessorPipeline(),
            DefaultExplainingPipeline(),
            auto_trace.get_loaded(),
        )
        self.assert_test_case(
            datadir,
            "constraint1",
            ConstraintRelaxerPipeline(),
            DefaultExplainingPipeline(),
            lp_extensions=constraints.get_loaded(),
        )
        self.assert_test_case(
            datadir,
            "count_aggregate",
            PreprocessorPipeline(),
            DefaultExplainingPipeline(),
        )
        self.assert_test_case(
            datadir,
            "diamond_with_mute",
            PreprocessorPipeline(),
            DefaultExplainingPipeline(),
        )
        self.assert_test_case(
            datadir,
            "dont_drive_drunk",
            PreprocessorPipeline(),
            DefaultExplainingPipeline(),
        )
        self.assert_test_case(
            datadir,
            "ignore_shows",
            PreprocessorPipeline(),
            DefaultExplainingPipeline(),
            lp_extensions=auto_trace.get_loaded(),
        )
        self.assert_test_case(
            datadir,
            "pool_and_choice",
            PreprocessorPipeline(),
            DefaultExplainingPipeline(),
        )
        self.assert_test_case(
            datadir,
            "pool_and_choice2",
            PreprocessorPipeline(),
            DefaultExplainingPipeline(),
        )
