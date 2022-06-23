%%%%%%%%%%%%%% xclingo_graph.lp %%%%%%%%%%%%%%%%%

% Complete explanation graph (includes non labelled atoms)
_xclingo_graph(complete_explanation).
_xclingo_node(Atom, complete_explanation) :- _xclingo_audible(Atom).  %TODO: remove f_atom in favor of node
_xclingo_edge((Caused, Cause), complete_explanation) :-
    _xclingo_inbody((Cause, Body)), 
    _xclingo_f(_, Caused, Body),
    _xclingo_f(_, Cause, _),
    _xclingo_audible(Cause).

% Compressing graph (only labelled; and show_trace Atoms even if they are not labelled)
_xclingo_visible(X) :- _xclingo_node(X, complete_explanation), _xclingo_label(X, _).
%
_xclingo_skip(X, Y) :- _xclingo_edge((X, Y), complete_explanation), not _xclingo_visible(X).
_xclingo_skip(X, Y) :- _xclingo_edge((X, Y), complete_explanation), not _xclingo_visible(Y).
%
_xclingo_reach(X, Z) :- _xclingo_skip(X, Z).
_xclingo_reach(X, Z) :- _xclingo_reach(X, Y), _xclingo_skip(Y, Z), not _xclingo_visible(Y).
%

% Explanation (compressed) graph
_xclingo_graph(explanation).
_xclingo_edge((Caused, Cause), explanation) :- _xclingo_edge((Caused, Cause), complete_explanation), not _xclingo_skip(Caused, Cause).
_xclingo_edge((Caused, Cause), explanation) :- _xclingo_reach(Caused, Cause), _xclingo_visible(Caused), _xclingo_visible(Cause).
_xclingo_edge((ToExplainAtom, Cause), explanation) :- _xclingo_reach(ToExplainAtom, Cause), _xclingo_visible(Cause), _xclingo_show_trace(ToExplainAtom).
_xclingo_node(Caused, explanation) :- _xclingo_visible(Caused).
_xclingo_node(ToExplainAtom, explanation) :- _xclingo_show_trace(ToExplainAtom).

% Labels
_xclingo_attr(node, Atom, label, Label) :- _xclingo_label(Atom, Label), _xclingo_node(Atom, explanation).
