import pytest

from xclingo.preprocessor._utils import translate_show_all, translate_trace_all, translate_trace

class TestUtils:

    def test_translate_trace_all(self, datadir):
        input_text = (datadir / 'test_trace_all_input').read_text()
        expected_text = (datadir / 'test_trace_all_output').read_text()
        translated = translate_trace_all(input_text)
        assert expected_text == translated

    def test_translate_show_all(self, datadir):
        input_text = (datadir / 'test_show_all_input').read_text()
        expected_text = (datadir / 'test_show_all_output').read_text()
        translated = translate_show_all(input_text)
        assert expected_text == translated

    def test_translate_trace(self, datadir):
        input_text = (datadir / 'test_trace_input').read_text()
        expected_text = (datadir / 'test_trace_output').read_text()
        translated = translate_trace(input_text)
        print(translated)
        print('--------')
        print(expected_text)
        assert expected_text == translated
