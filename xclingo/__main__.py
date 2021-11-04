from xclingo import Explainer as Explainer
from clingo import Control
import sys

def check_options():
    i_file=1
    while(sys.argv[i_file].isnumeric()):
        i_file+=1
    clingo_n = sys.argv[1] if i_file > 1 else '1'
    xclingo_n = sys.argv[2] if i_file > 2 else '1'
    files = sys.argv[i_file:]
    return clingo_n, xclingo_n, files

def read_files(files):
    program=""
    for filepath in files:
        with open(filepath, "r") as pfile:
            program += pfile.read()
    return program

def main():
    clingo_n, xclingo_n, files = check_options()
    program = read_files(files)

    control = Control([clingo_n])
    explainer = Explainer([xclingo_n])

    explainer.add('base', [], program)
    control.add("base", [], program)
    control.ground([("base", [])])

    nanswer=1
    with control.solve(yield_=True) as it:
        print(f'Answer {nanswer}')
        for m in it:
            explainer.explain(m)
        nanswer+=1

if __name__ == '__main__':
    main()
