max(8).
p(0).


a(N) :- p(N),N<M,max(M).
b(N) :- p(N), N<M,max(M).

p(N+1) :- a(N), N<M,max(M).
p(N+1) :- b(N), N<M,max(M).

%!trace {"p(%)",N} p(N).
%!trace {"a(%)", N} a(N).
%!trace {"b(%)", N} b(N).
%!show_trace p(N): max(N).

% enable/disable the %!mute annotations and see the effects
% --> add/delete 'spaces' between '%' and '!'
%!mute p(3).

