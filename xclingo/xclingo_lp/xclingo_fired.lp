%%%%%%%%%%%%%% xclingo_fired.lp %%%%%%%%%%%%%%%%%

% Marks relevant atoms of the program, with respect of the atoms that must be explained.
_xclingo_relevant(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom).
_xclingo_relevant(R) :- _xclingo_sup_cause(Sup, R), Sup=_xclingo_sup(RuleID, DisID, Atom, Vars), _xclingo_relevant(Atom), _xclingo_model(R).

% Decides which rule fire each relevant atom (must be one and only one).
1{_xclingo_f(RuleID, D, Atom, Vars) : _xclingo_fbody(RuleID, D, Atom, Vars)}1 :- _xclingo_relevant(Atom).
:- _xclingo_f(R,D1,_,_), _xclingo_f(R,D2,_,_), D1!=D2.

_xclingo_f_atom(Atom) :- _xclingo_f(_, _, Atom, _).
