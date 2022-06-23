%%%%%%%%%%%%%% xclingo_fired.lp %%%%%%%%%%%%%%%%%
% 
_xclingo_inbody(@inbody(Body)) :- _xclingo_sup(_, _, Body).

% Marks relevant atoms of the program, with respect of the atoms that must be explained.
_xclingo_relevant(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom).
_xclingo_relevant(R) :- _xclingo_inbody((R, Body)), _xclingo_sup(_, Atom, Body), _xclingo_relevant(Atom), _xclingo_model(R).

% Decides which rule fire each relevant atom (must be one and only one).
1{_xclingo_f(RuleID, Atom, Body) : _xclingo_fbody(RuleID, Atom, Body)}1 :- _xclingo_relevant(Atom).
_xclingo_f_atom(Atom) :- _xclingo_f(_, Atom, _).

% Not muted part of the current graph
_xclingo_audible(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom), not _xclingo_muted(ToExplainAtom).
_xclingo_audible(R) :- _xclingo_inbody((R, Body)), _xclingo_f(_, Atom, Body), _xclingo_audible(Atom), not _xclingo_muted(R).
% _xclingo_audible(Atom) :- _xclingo_f(RuleID, Atom, Body).
