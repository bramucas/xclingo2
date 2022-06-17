#show.
#show _xclingo_edge((Caused, Cause), Graph) : _xclingo_edge((Caused, Cause), Graph), Graph=explanation.
#show _xclingo_attr(Type, Atom, Attr, Label) : _xclingo_attr(Type, Atom, Attr, Label), Type=node, Attr=label, _xclingo_node(Atom, explanation).

#project _xclingo_edge((Caused, Cause), Graph) : _xclingo_edge((Caused, Cause), Graph), Graph=explanation.
#project _xclingo_attr(Type, Atom, Attr, Label) : _xclingo_attr(Type, Atom, Attr, Label), Type=node, Attr=label, _xclingo_node(Atom, explanation).
