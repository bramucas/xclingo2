%%%%%%%%%%%%%% xclingo_show.lp %%%%%%%%%%%%%%%%%
#show.
% All show traces
#show _xclingo_show_trace(Atom) : _xclingo_show_trace(Atom), _xclingo_node(Atom, Graph), Graph=complete_explanation.
#project _xclingo_show_trace(Atom) : _xclingo_show_trace(Atom), _xclingo_node(Atom, Graph), Graph=explanation.
% Which causes explain not visible show_traces
% #show _xclingo_link(ToExplainAtom, Cause) : _xclingo_link(ToExplainAtom, Cause).
% #project _xclingo_link(ToExplainAtom, Cause) : _xclingo_link(ToExplainAtom, Cause).

% Edges of the explanation
#show _xclingo_edge((Caused, Cause), Graph) : _xclingo_edge((Caused, Cause), Graph), Graph=explanation.
#project _xclingo_edge((Caused, Cause), Graph) : _xclingo_edge((Caused, Cause), Graph), Graph=explanation.
% Labels
#show _xclingo_attr(Type, Atom, Attr, Label) : _xclingo_attr(Type, Atom, Attr, Label), Type=node, Attr=label, _xclingo_node(Atom, explanation).
#project _xclingo_attr(Type, Atom, Attr, Label) : _xclingo_attr(Type, Atom, Attr, Label), Type=node, Attr=label, _xclingo_node(Atom, explanation).
