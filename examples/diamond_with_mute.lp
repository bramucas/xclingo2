max(4).
p(0).

%!trace_rule {"a(%)",N}
a(N) :- p(N),N<M,max(M).

%!trace_rule {"b(%)",N}
b(N) :- p(N), N<M,max(M).

p(N+1) :- a(N), N<M,max(M).
p(N+1) :- b(N), N<M,max(M).
%!trace {"p(%)",N} p(N).

%!show_trace p(N):max(N).

% enable/disable the %!mute annotations and see the effects
% --> add/delete 'spaces' between '%' and '!'
%!mute a(2).
% !mute p(N) : N=1.
