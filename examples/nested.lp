
a(1,a).

%!trace_rule {"b(a(%,%))", X,Y}.
b(a(X,Y)) :- a(X,Y).

%!trace {a(X,Y), "a(%,%).", X, Y}.

%!show_trace {b(X)}.
