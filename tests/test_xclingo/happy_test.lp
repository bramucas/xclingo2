person(manuel;gabriel;clare;robert).

healthy(manuel;clare,gabriel).

friend(manuel,gabriel).
friend(manuel,clare).
friend(manuel,robert).

friend(robert,manuel).
friend(robert,gabriel).
friend(robert,clare).

%!trace_rule {"% has at least 3 friends",X}.
has3(X) :- #count{Y: friend(X,Y), Y!=X}>=3, person(X).
%!trace_rule {"% is happy", X}.
happy(X) :- healthy(X), has3(X).

%!trace {friend(X,Y), "% and % are friends", X, Y} :- friend(X,Y).
%!trace {healthy(X), "% is healthy", X} :- healthy(X).

%!show_trace {happy(X)} :- happy(X).
#show happy/1.
