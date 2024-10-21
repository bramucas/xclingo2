%%%%%%%%%%%%%% xclingo_fired.lp %%%%%%%%%%%%%%%%%

% Marks relevant atoms of the program, with respect of the atoms that must be explained.
_xclingo_relevant(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom).
_xclingo_relevant(Cause) :- _xclingo_relevant(Effect), _xclingo_depends(_xclingo_sup(R, D, Effect, Vars), Cause).

%%%% fireable if it fact
_xclingo_fbody(RuleID, D, Atom, Vars) :- _xclingo_relevant(Atom), _xclingo_sup(RuleID, D, Atom, Vars), not _xclingo_depends(_xclingo_sup(RuleID, D, _, _), _).
%%%% _xclingo_fbody if 
_xclingo_fbody(R, D, Atom, Vars) :- 
    _xclingo_sup(R, D, Atom, Vars), 
    _xclingo_f_atom(Cause) : _xclingo_depends(_xclingo_sup(R, D, Atom, Vars), Cause).

% Decides which rule fire each relevant atom (must be one and only one).
1{_xclingo_f(RuleID, D, Atom, Vars) : _xclingo_fbody(RuleID, D, Atom, Vars)}1 :- _xclingo_relevant(Atom).
% Two elements from the same disyunction cannot be selected
:- _xclingo_f(R,D1,_,_), _xclingo_f(R,D2,_,_), D1!=D2.


_xclingo_f_atom(Atom) :- _xclingo_f(_, _, Atom, _).

_xclingo_direct_cause(RuleID, Effect, Cause) :- _xclingo_f(RuleID, DisID, Effect, Vars), _xclingo_depends(_xclingo_sup(RuleID, DisID, Effect, Vars), Cause).
