max(3).
p(0).

%!trace_rule {"a(%)",N}
a(N) :- p(N),N<M,max(M).

%!trace_rule {"b(%)",N}
b(N) :- p(N), N<M,max(M).

p(N+1) :- a(N), N<M,max(M).
p(N+1) :- b(N), N<M,max(M).
%!trace {"p(%)",N} p(N).

%!show_trace p(N):max(N).
