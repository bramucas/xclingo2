% TODO: tuples
_xclingo_inbody(@inbody(Body)) :- _xclingo_sup(_, _, Body).

% Which atom to explain
1 {_xclingo_to_explain(A) : _xclingo_show_trace(A)} 1.

% Whcih atom to use for explain it.
_xclingo_relevant(ToExplainAtom) :- _xclingo_to_explain(ToExplainAtom).
_xclingo_relevant(R) :- _xclingo_inbody((R, Body)), _xclingo_sup(_, Atom, Body), _xclingo_relevant(Atom), _xclingo_model(R).
%%%%%%%%%%%%%%%%%%%%%

% Generates explanations.
1{_xclingo_f(ID, Atom, Body) : _xclingo_fbody(ID, Atom, Body)}1 :- _xclingo_relevant(Atom).
_xclingo_f_atom(Atom) :- _xclingo_f(_, Atom, _).

% Atom tree
_xclingo_child(root, ToExplainAtom) :- _xclingo_f(_, ToExplainAtom, _), _xclingo_to_explain(ToExplainAtom).
_xclingo_child(Caused, Cause) :- _xclingo_inbody((Cause, Body)), _xclingo_f(_, Caused, Body), _xclingo_child(_, Caused).
_xclingo_intree(X;Y) :- _xclingo_child(X,Y).

% Label tree
_xclingo_skip(X, Y) :- _xclingo_child(X, Y), not _xclingo_label(X, _), X!=root.
_xclingo_skip(X, Y) :- _xclingo_child(X, Y), not _xclingo_label(Y, _).
%
_xclingo_reach(X, Z) :- _xclingo_skip(X, Z).
_xclingo_reach(X, Z) :- _xclingo_skip(X, Y), _xclingo_reach(Y, Z).
%
_xclingo_label_tree(X, Y, Label) :- _xclingo_child(X, Y), not _xclingo_skip(X, Y), _xclingo_label(Y, Label).
_xclingo_label_tree(X, Y, Label) :- _xclingo_reach(X,Y), _xclingo_label(Y, Label), _xclingo_label(X, _).


% Necesitamos todo?
% cause(IDCause, ToExplainAtom, root, root) :- f(IDCause, ToExplainAtom, _), to_explain(ToExplainAtom).
% cause(IDCause, Cause, Caused, IDCaused) :- f(IDCause, Cause, _), inbody((Cause, Body)), f(IDCaused, Caused, Body).
% cause(true, true,  Caused, ID) :- f(ID, Caused, empty).

% #show _xclingo_to_explain/1.
#show _xclingo_label_tree/3.

