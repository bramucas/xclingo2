#const maxn=4.
p(0).


a(N) :- p(N),N<maxn.
b(N) :- p(N), N<maxn.

p(N+1) :- a(N), N<maxn.
p(N+1) :- b(N), N<maxn.

%!trace {"p(%)",N} p(N).
%!trace {"a(%)", N} a(N).
%!trace {"b(%)", N} b(N).
%!show_trace p(maxn).

% enable/disable the %!mute annotations and see the effects
% --> add/delete 'spaces' between '%' and '!'
%!mute p(3).

