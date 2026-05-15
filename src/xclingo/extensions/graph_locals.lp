% Local graphs (one per each 'toexplain' atom)
_xclingo_graph(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom).

% Add a node for ToExplainAtom, even if not visible
_xclingo_node(ToExplainAtom, ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom).

% Any node in an edge is a node.
_xclingo_node(Cause, ToExplainAtom) :- _xclingo_edge((_, Cause), ToExplainAtom), _xclingo_show_trace(ToExplainAtom).

% Add an edge if it exists for 'explanation'
_xclingo_edge((Caused, Cause), ToExplainAtom):-
    _xclingo_edge((Caused, Cause), explanation),
    _xclingo_node(Caused, ToExplainAtom),
    _xclingo_show_trace(ToExplainAtom).
