table(a). leg(a,1). leg(a,2). leg(a,3).
table(b). leg(b,(1..5)).

%!trace_rule {"Table % is unbalanced", X}.
unbalanced(X) :- table(X), #count{Y:leg(X,Y)}<4.

%!show_trace {unbalanced(X)} :- unbalanced(X).
#show unbalanced/1.
