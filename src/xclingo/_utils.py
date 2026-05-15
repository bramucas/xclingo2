from ._version import __version__ as xclingo_version


def print_version():
    print(f"xclingo version {xclingo_version}")


def print_header(args):
    print_version()
    print(f"Reading from {' '.join([f.name for f in args.infiles])}")
