class ExplanationControlError(RuntimeError):
    pass


class ExplanationControlParsingError(ExplanationControlError):
    pass


class ExplanationControlGroundingError(ExplanationControlError):
    pass
