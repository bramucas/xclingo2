from clingo import Function, String
from clingo.symbol import SymbolType

try:
    from importlib.resources import read_text
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    from importlib_resources import read_text

from .. import xclingo_lp


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

    def inbody(self, body):
        """Handles the inbody/2 predicate from the xclingo_lp program."""
        if len(body.arguments) > 0:
            return [
                Function(
                    "",
                    [a, body],
                    True,
                )
                for a in body.arguments
            ]
        else:
            return Function("empty", [], True)


class LPLoader:
    def __init__(self):
        self.cache = None

    def _loadExplainerLP(self):
        if self.cache is None:
            self.cache = (
                read_text(xclingo_lp, "xclingo_fired.lp")
                + read_text(xclingo_lp, "xclingo_graph.lp")
                + read_text(xclingo_lp, "xclingo_show.lp")
            )
        return self.cache
