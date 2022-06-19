try:
    from importlib.resources import read_text
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    from importlib_resources import read_text


class ExtensionLoader:
    def __init__(self):
        self.loaded = []

    def loadLPExtension(self, name: str):
        self.loaded.append(("base", read_text(__package__, resource=name)))

    def get_loaded(self):
        return self.loaded
