from clingo import Model

from argparse import ArgumentParser, FileType
import sys
from .._version import __version__ as xclingo_version


class FrozenModel:
    def __init__(self):
        self._mem = []

    @property
    def mem(self):
        return frozenset(self._mem)

    def save(self, m: Model):
        self._mem.append(frozenset(str(s) for s in m.symbols(shown=True)))

    def __eq__(self, other):
        return self.mem == other.mem

    def __init__(self):
        self._mem = []


def print_header(args):
    print(f"xclingo version {xclingo_version}")
    print(f"Reading from {' '.join([f.name for f in args.infiles])}")


def check_options():
    """Handles arguments of xclingo"""
    parser = ArgumentParser(
        description="Tool for explaining (and debugging) ASP programs", prog="xclingo"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="xclingo {version}".format(version=xclingo_version),
        help="Prints the version and exists.",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=[
            "ascii-trees",
            "translation",
            "graph-models",
        ],
        default="ascii-trees",
        help="""Determines the format of the output. "translation" will output the translation 
        together with the xclingo logic program. "graph-models" will output the explanation 
        graphs following clingraph format.""",
    )
    parser.add_argument(
        "--picklefile",
        type=str,
        help="""""",
    )
    parser.add_argument(
        "--auto-tracing",
        type=str,
        choices=["none", "facts", "all"],
        default="none",
        help="""Automatically creates traces for the rules of the program. Default: none.
        - 'facts' will create labels for every fact rule in the program.
        - 'all' will create labels for every rule in the program.""",
    )
    parser.add_argument(
        "--constraint-explaining",
        type=str,
        choices=["minimize", "all"],
        default="minimize",
        help="""Explains traced constraints of the program. Default: unsat.
        - 'unsat' will only explain constraints if original program is UNSAT. In such a case
        the ocurrence of violated constraints will be minimized when solving the original program.
        - 'minimize' acts as 'unsat' but the first UNSAT check is skipped. Directly minimizes the
        constraints when solving the original program. Useful when the original program is known
        UNSAT but it takes long to check it.
        - 'all' will explain all constraints and will not minimize them before explaining.""",
    )
    parser.add_argument(
        "-n",
        nargs=2,
        default=(1, 1),
        type=int,
        help="Number of answer sets and number of desired explanations.",
    )
    parser.add_argument(
        "infiles", nargs="+", type=FileType("r"), default=sys.stdin, help="ASP program"
    )
    return parser.parse_args()
