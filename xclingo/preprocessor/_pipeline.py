from ._preprocessor import Preprocessor
from ._preprocessor import XClingoAnnotationPreprocessor
from ._preprocessor import ConstraintRelaxer
from ._preprocessor import XClingoPreprocessor


class PreprocessorPipeline:
    def __init__(self):
        self.preprocessors = list()

    def register_at_beginning(self, preprocessor: Preprocessor):
        self.preprocessors.insert(0, preprocessor)

    def register_at_end(self, preprocessor: Preprocessor):
        self.preprocessors.append(preprocessor)

    def translate(self, name: str, program: str):
        translation = program
        for p in self.preprocessors:
            translation = p.process_program(translation)
        return f"%%%%%%%% {name} %%%%%%%%\n{translation}"


class ConstraintRelaxerPipeline(PreprocessorPipeline):
    MINIMIZE_STATEMENT = '\n#minimize{1,ID, Vars: _xclingo_violated_constraint(ID, Vars)}.'
    
    def __init__(self):
        super().__init__()
        self.register_at_end(XClingoAnnotationPreprocessor())
        self.register_at_end(ConstraintRelaxer())

    def translate(self, name: str, program: str):
        return super().translate(name, program) + self.MINIMIZE_STATEMENT


class DefaultExplainingPipeline(PreprocessorPipeline):
    def __init__(self):
        super().__init__()
        self.register_at_end(XClingoAnnotationPreprocessor())
        self.register_at_end(XClingoPreprocessor())


class ConstraintExplainingPipeline(PreprocessorPipeline):
    def __init__(self):
        super().__init__()
        self.register_at_end(XClingoAnnotationPreprocessor())
        self.register_at_end(ConstraintRelaxer(keep_annotations=True))
        self.register_at_end(XClingoPreprocessor())
