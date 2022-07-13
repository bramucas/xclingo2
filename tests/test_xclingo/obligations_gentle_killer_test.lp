%%%%%%%%%%%%%%%%% gentle_killer.lp

% I have the obligation not to kill
obl(kill,false).

% CTD: If violate the obligation to kill, I have the obligation to kill gently
obl(kill_gently,true) :- viol(kill,false).

% killing gently counts as killing
h(kill,true) :- h(kill_gently,true).
obl(kill,true) :- obl(kill_gently,true).

%!trace_rule {"I decided to kill"}.
h(kill,true).

%%%%%%%%%%%%%%%%%% obligations.lp

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

