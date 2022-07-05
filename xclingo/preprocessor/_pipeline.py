from ._preprocessor import Preprocessor
from ._preprocessor import XClingoAnnotationPreprocessor
from ._preprocessor import ConstraintRelaxer
from ._preprocessor import XClingoPreprocessor

from ._utils import (
    translate_show_all,
    translate_trace,
    translate_trace_all,
    translate_mute,
)


class PreprocessorPipeline:
    def __init__(self):
        self.preprocessors = list()

    def register_preprocessor(self, preprocessor: Preprocessor):
        self.preprocessors.append(preprocessor)

    def translate(self, name: str, program: str):
        translation = program
        for p in self.preprocessors:
            translation = p.process_program(translation)
        return f"%%%%%%%% {name} %%%%%%%%\n{translation}"


class ConstraintRelaxerPipeline(PreprocessorPipeline):
    def __init__(self):
        super().__init__()
        self.register_preprocessor(XClingoAnnotationPreprocessor())
        self.register_preprocessor(ConstraintRelaxer(preserve_labels=False))


class DefaultExplainingPipeline(PreprocessorPipeline):
    def __init__(self):
        super().__init__()
        self.register_preprocessor(XClingoAnnotationPreprocessor())
        self.register_preprocessor(XClingoPreprocessor())
