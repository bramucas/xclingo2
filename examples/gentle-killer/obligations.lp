
opp(false,true). opp(true,false).

% Agents that follow their obligations by default
% If I have an obligation, I follow it by default
%h(P,V) :- obl(P,V),opp(V,V'), not h(P,V').

% I cannot have two values for a same predicate
:- h(P,V), h(P,V'), V!=V'.

% I cannot have obligation of P and -P at the same time, unless one of them is violated
:- obl(P,V), obl(P,V'), V!=V', not h(P,V), not h(P,V').

% perm(P) is equivalent to -obl(-P)
perm(P,V) :- opp(V,V'), -obl(P,V').
-obl(P,V) :- opp(V,V'), perm(P,V').

% Violation
viol(P,V) :- obl(P,V), h(P,V'), V!=V'.

% Follwing an obligation
follow(P,V) :- obl(P,V), h(P,V).

%!trace {obl(P,V),"obligation: %=%",P,V} :- obl(P,V).
%!trace {h(P,V), "holds: %=%",P,V} :- h(P,V).
%!trace {viol(P,V),"violation of obligation: %=%",P,V} :- viol(P,V).
%!trace {perm(P,V),"permission: %=%",P,V} :- perm(P,V).

%!show_trace {viol(P,V)} :- viol(P,V).
%!show_trace {h(P,V)} :- h(P,V).
%!show_trace {obl(P,V)} :- obl(P,V).
%!show_trace {perm(P,V)} :- perm(P,V).
