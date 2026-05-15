try:
    from importlib.resources import read_text
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    from importlib_resources import read_text

FIRED_LP = read_text(__package__, "xclingo_fired.lp")
GRAPH_LP = read_text(__package__, "xclingo_graph.lp")
SHOW_LP = read_text(__package__, "xclingo_show.lp")
