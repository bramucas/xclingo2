from clingo import Function, String
from clingo.symbol import SymbolType


class XClingoContext:
    """Xclingo context class."""

    def label(self, text, tup):
        """Given the text of a label and a tuple of symbols, handles the variable instantiation
        and returns the processed text label."""
        if text.type == SymbolType.String:
            text = text.string
        else:
            text = str(text).strip('"')
        for val in tup.arguments:
            text = text.replace("%", val.string if val.type == SymbolType.String else str(val), 1)
        return [String(text)]
