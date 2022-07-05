a(1..30).

%!trace {a(X), "a(%)", X} :- a(X).

%!show_trace {a(X)} :- a(X), X\2=0.
