%% Always show trace of violated constraints
_xclingo_show_trace(_xclingo_violated_constraint(ID, Vars)) :- _xclingo_model(_xclingo_violated_constraint(ID, Vars)).
