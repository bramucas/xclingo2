%%%%%%%%%%%%%% xclingo.lp %%%%%%%%%%%%%%%%%
_xclingo_inbody(@inbody(Body)) :- _xclingo_sup(_, _, Body).

% Marks relevant atoms of the program, with respect of the atoms that must be explained.
_xclingo_relevant(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom).
_xclingo_relevant(R) :- _xclingo_inbody((R, Body)), _xclingo_sup(_, Atom, Body), _xclingo_relevant(Atom), _xclingo_model(R).

% Decides which rule fire each relevant atom (must be one and only one).
1{_xclingo_f(RuleID, Atom, Body) : _xclingo_fbody(RuleID, Atom, Body)}1 :- _xclingo_relevant(Atom).
_xclingo_f_atom(Atom) :- _xclingo_f(_, Atom, _).

% Decides which part of the graph is visible, having %!mute into account.
% (relevant/1 for the currently considered (fired) program)
_xclingo_visible(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom), not _xclingo_muted(ToExplainAtom).
_xclingo_visible(R) :- _xclingo_inbody((R, Body)), _xclingo_f(_, Atom, Body), _xclingo_visible(Atom), not _xclingo_muted(R).
% _xclingo_visible(Atom) :- _xclingo_f(RuleID, Atom, Body).

% Complete explanation graph
_xclingo_graph(complete_explanation).
_xclingo_node(Atom, complete_explanation) :- _xclingo_visible(Atom).  %TODO: remove f_atom in favor of node
_xclingo_edge((Caused, Cause), complete_explanation) :-
    _xclingo_inbody((Cause, Body)), 
    _xclingo_f(_, Caused, Body),
    _xclingo_f(_, Cause, _),
    _xclingo_visible(Cause).

% Compressing graph
_xclingo_marked(X) :- _xclingo_node(X, complete_explanation), _xclingo_label(X, _).
%
_xclingo_skip(X, Y) :- _xclingo_edge((X, Y), complete_explanation), not _xclingo_marked(X).
_xclingo_skip(X, Y) :- _xclingo_edge((X, Y), complete_explanation), not _xclingo_marked(Y).
%
_xclingo_reach(X, Z) :- _xclingo_skip(X, Z).
_xclingo_reach(X, Z) :- _xclingo_reach(X, Y), _xclingo_skip(Y, Z), not _xclingo_marked(Y).


% Explanation (compressed) graph
_xclingo_graph(explanation).
_xclingo_edge((Caused, Cause), explanation) :- _xclingo_edge((Caused, Cause), complete_explanation), not _xclingo_skip(Caused, Cause).
_xclingo_edge((Caused, Cause), explanation) :- _xclingo_reach(Caused, Cause), _xclingo_marked(Caused), _xclingo_marked(Cause).
_xclingo_node(Caused, explanation) :- _xclingo_marked(Caused).

_xclingo_attr(node, Atom, label, Label) :- _xclingo_label(Atom, Label), _xclingo_node(Atom, complete_explanation).

#show.
#show _xclingo_edge((Caused, Cause), Graph) : _xclingo_edge((Caused, Cause), Graph), Graph=explanation.
#show _xclingo_attr(Type, Atom, Attr, Label) : _xclingo_attr(Type, Atom, Attr, Label), Type=node, Attr=label, _xclingo_node(Atom, explanation).

% Necesitamos todo?
% cause(IDCause, ToExplainAtom, root, root) :- f(IDCause, ToExplainAtom, _), to_explain(ToExplainAtom).
% cause(IDCause, Cause, Caused, IDCaused) :- f(IDCause, Cause, _), inbody((Cause, Body)), f(IDCaused, Caused, Body).
% cause(true, true,  Caused, ID) :- f(ID, Caused, empty).


#project _xclingo_edge((Caused, Cause), Graph) : _xclingo_edge((Caused, Cause), Graph), Graph=explanation.
#project _xclingo_attr(Type, Atom, Attr, Label) : _xclingo_attr(Type, Atom, Attr, Label), Type=node, Attr=label, _xclingo_node(Atom, explanation).