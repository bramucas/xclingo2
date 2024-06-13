a(1..10).

b(N) :- a(N).

%!trace {a(N), "this is a %", N}.

%!show_trace {b(N)}.