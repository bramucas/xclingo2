from clingo.core import MessageCode


class XclingoLogger:
    def __init__(self) -> None:
        self._no_labels = None
        self._no_show_trace = None

    def logger(self, _code, msg):
        """Logger TODO: more detail."""
        if _code == MessageCode.AtomUndefined:
            if "xclingo_muted" in msg:
                return
            if "_xclingo_label" in msg:
                self._no_labels = True
                return
            if "_xclingo_show_trace" in msg:
                self._no_show_trace = True
        print(msg)

    def print_messages(self):
        """Prints messages from the logger."""
        if self._no_labels:
            print("xclingo info: any atom or rule has been labelled.")
        if self._no_show_trace:
            print("xclingo info: any atom has been affected by a %!show_trace annotation.")
