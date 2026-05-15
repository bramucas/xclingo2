try:
    from importlib.resources import read_text
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    from importlib_resources import read_text


def load_xclingo_extension(extension_filename: str):
    return read_text(__package__, resource=extension_filename)
