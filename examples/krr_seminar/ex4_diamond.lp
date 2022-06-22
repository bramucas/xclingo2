max(5).
p(0).

a(N) :- p(N),N<M,max(M).
b(N) :- p(N), N<M,max(M).

p(N+1) :- a(N), N<M,max(M).
p(N+1) :- b(N), N<M,max(M).

%!show_trace p(N):max(N).

%!mute max(N).
%!mute p(3).
