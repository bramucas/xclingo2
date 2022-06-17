%% Always show trace of violated constraints
_xclingo_show_trace(_xclingo_violated_constraint(ID, B)) :- _xclingo_model(_xclingo_violated_constraint(ID, B)).
