person(gabriel;clare).

drive(gabriel).
alcohol(gabriel, 40).
resist(gabriel).

drive(clare).
alcohol(clare, 5).

%!trace_rule {"% drove drunk, which is punishable", P}.
punish(P) :- drive(P), alcohol(P,A), A>30, person(P).

%!trace {punish(P), "% was punished", P} :- punish(P).

%!trace_rule {"% resisted to authority, which is punishable", P}.
punish(P) :- resist(P), person(P).

% !trace_rule {"% goes to prison",P}.

%!trace {sentence(P,S), "% has been sentenced to %",P,S} :- sentence(P,S).

sentence(P, prison), sentence(P, bail) :- punish(P).

%  !trace_rule {"% is innocent by default",P}.
sentence(P, innocent) :- person(P), not punish(P).

%!trace {alcohol(P,A), "% alcohol's level is %",P,A} :- alcohol(P,A), A>30.
%!trace {alcohol(P,A), "% was drunk",P} :- alcohol(P,A).

%!show_trace {sentence(P,S)} :- sentence(P,S).
#show sentence/2.
