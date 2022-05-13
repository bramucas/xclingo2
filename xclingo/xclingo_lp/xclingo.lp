%%%%%%%%%%%%%% xclingo.lp %%%%%%%%%%%%%%%%%
% TODO: tuples
_xclingo_inbody(@inbody(Body)) :- _xclingo_sup(_, _, Body).

% Which atom to explain
1 {_xclingo_to_explain(A) : _xclingo_show_trace(A)} 1.

% Whcih atom to use for explain it.
_xclingo_relevant(ToExplainAtom) :- _xclingo_to_explain(ToExplainAtom).
_xclingo_relevant(R) :- _xclingo_inbody((R, Body)), _xclingo_sup(_, Atom, Body), _xclingo_relevant(Atom), _xclingo_model(R).
%%%%%%%%%%%%%%%%%%%%%

% Generates explanations.
1{_xclingo_f(RuleID, Atom, Body) : _xclingo_fbody(RuleID, Atom, Body)}1 :- _xclingo_relevant(Atom).
_xclingo_f_atom(Atom) :- _xclingo_f(_, Atom, _).

% Atom tree
_xclingo_child(root, ToExplainAtom) :- _xclingo_f(_, ToExplainAtom, _), _xclingo_to_explain(ToExplainAtom).
_xclingo_child(Caused, Cause) :- not _xclingo_muted(Cause), _xclingo_inbody((Cause, Body)), _xclingo_f(_, Caused, Body), _xclingo_child(_, Caused).
_xclingo_intree(X;Y) :- _xclingo_child(X,Y).

% Label tree
_xclingo_marked(X) :- _xclingo_label(X, _).
_xclingo_marked(root).
%
_xclingo_skip(X, Y) :- _xclingo_child(X, Y), not _xclingo_label(X, _).
_xclingo_skip(X, Y) :- _xclingo_child(X, Y), not _xclingo_label(Y, _).
%
_xclingo_reach(X, Z) :- _xclingo_skip(X, Z).
_xclingo_reach(X, Z) :- _xclingo_reach(X, Y), _xclingo_skip(Y, Z), not _xclingo_marked(Y).
%
_xclingo_tree(P, C) :- _xclingo_child(P, C), not _xclingo_skip(P, C).
_xclingo_tree(P, C) :- _xclingo_reach(P, C), _xclingo_marked(P), _xclingo_marked(C).
%
_xclingo_label_tree(X, Y, Label) :- _xclingo_tree(X, Y), _xclingo_label(Y, Label).

% for projection
_xclingo_label_tree(root, ChildLabel) :- _xclingo_label_tree(root, C, ChildLabel).
_xclingo_label_tree(ParentLabel, ChildLabel) :- _xclingo_label_tree(PP, P, ParentLabel), _xclingo_label_tree(P, C, ChildLabel).

% Necesitamos todo?
% cause(IDCause, ToExplainAtom, root, root) :- f(IDCause, ToExplainAtom, _), to_explain(ToExplainAtom).
% cause(IDCause, Cause, Caused, IDCaused) :- f(IDCause, Cause, _), inbody((Cause, Body)), f(IDCaused, Caused, Body).
% cause(true, true,  Caused, ID) :- f(ID, Caused, empty).

#show _xclingo_label_tree/3.
#project _xclingo_label_tree/2.
