person(gabriel;clare).

drive(gabriel).
alcohol(gabriel, 40).
resist(gabriel).

drive(clare).
alcohol(clare, 5).

%!trace_rule {"% drove drunk", P}
punish(P) :- drive(P), alcohol(P,A), A>30, person(P).

%!trace_rule {"% resisted to authority", P}
punish(P) :- resist(P), person(P).

%!trace_rule {"% goes to prison",P}
sentence(P, prison) :- punish(P).

%!trace_rule {"% is innocent by default",P}
sentence(P, innocent) :- person(P), not punish(P).

%!trace {"% alcohol's level is %",P,A} alcohol(P,A).
%!trace {"% was drunk",P} alcohol(P,A).

%!show_trace sentence(P,S).