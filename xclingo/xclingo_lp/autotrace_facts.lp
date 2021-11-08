% Genrerates a label for each fact atom in the explanation
_xclingo_label(Head, Head) :- _xclingo_child(_, Head), _xclingo_fbody(_, Head, ()).
