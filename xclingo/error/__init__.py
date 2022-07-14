class ModelControlError(RuntimeError):
    pass


class ModelControlParsingError(ModelControlError):
    pass


class ModelControlGroundingError(ModelControlError):
    pass
