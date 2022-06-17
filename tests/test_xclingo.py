import pytest

from xclingo import XclingoControl


class TestXclingo:
    """System test. From input to expected output."""

    def assert_test_case(self, datadir, test_case, auto_tracing):
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
            n_solutions=0,
            n_explanations=0,
            auto_trace=auto_tracing,
        )
        xcontrol.add("base", [], (datadir / f"{test_case}.lp").read_text())
        xcontrol.ground()

        result = xcontrol._default_output()
        expected = (datadir / f"expected_{test_case}.txt").read_text()
        print(result)
        assert expected == result

    def test_test_cases(self, datadir):
        """This test function should test all the tests within the test_xclingo/ dir.

        It has to be updated every time a test is added
        """
        self.assert_test_case(datadir, "count_aggregate", "none")
        self.assert_test_case(datadir, "ignore_shows", "all")
