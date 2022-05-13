import pytest

from xclingo import XclingoControl, XclingoContext

class TestXclingo:

    def assert_test_case(self, datadir, test_case, auto_tracing):
        xcontrol = XclingoControl(
            n_solutions=0,
            n_explanations=0,
            auto_trace=auto_tracing,
        )
        xcontrol.add('base', [], (datadir / f'{test_case}.lp').read_text())
        xcontrol.ground()
        
        result = xcontrol._default_output()
        expected = (datadir / f'expected_{test_case}.txt').read_text()
        assert expected == result

    def test_count_aggregate(self, datadir):
        self.assert_test_case(datadir, 'count_aggregate', 'none')
        self.assert_test_case(datadir, 'ignore_shows', 'all')