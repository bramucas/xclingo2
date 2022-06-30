#const maxn=4.
p(0).

%!trace_rule {"a(%)", N}.
a(N) :- p(N),N<maxn.
%!trace_rule {"b(%)", N}.
b(N) :- p(N), N<maxn.

p(N+1) :- a(N), N<maxn.
p(N+1) :- b(N), N<maxn.

%!trace {p(N),"p(%)",N} :- p(N).
%!show_trace {p(MaxN)} :- p(MaxN), MaxN=maxn.

% enable/disable the %!mute annotations and see the effects
% --> add/delete 'spaces' between '%' and '!'
%!mute {p(3)}.

