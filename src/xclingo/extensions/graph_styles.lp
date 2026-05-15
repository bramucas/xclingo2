% Graphviz attributes: https://graphviz.org/doc/info/attrs.html

% Bottom to Top
_xclingo_attr(graph, Graph, rankdir, "BT") :- _xclingo_graph(Graph).
% Directed graph (now its 'backwards' because the encoding is in the opposite direction)
_xclingo_attr(edge, (Caused, Cause), dir, back) :- _xclingo_edge((Caused, Cause), Graph).

% Fill color for show trace nodes
% _xclingo_attr(node, ToExplainAtom, fillcolor, lightgreen) :- _xclingo_show_trace(ToExplainAtom).
% _xclingo_attr(node, ToExplainAtom, style, filled) :- _xclingo_show_trace(ToExplainAtom).
