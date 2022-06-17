% Tree graphs (one per each 'toexplain' atom)
_xclingo_graph(ToExplainAtom) :- _xclingo_show_trace(ToExplainAtom).
_xclingo_node(ToExplainAtom, ToExplainAtom) :- _xclingo_graph(ToExplainAtom), _xclingo_visible(ToExplainAtom).
_xclingo_edge((Caused, Cause), ToExplainAtom):-
    _xclingo_edge((Caused, Cause), explanation),
    _xclingo_node(Caused, ToExplainAtom),
    _xclingo_visible(Cause).    
_xclingo_node(Cause, ToExplainAtom) :- _xclingo_edge((_, Cause), ToExplainAtom).