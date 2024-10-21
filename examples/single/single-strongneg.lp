
spoused(barack,michelle).
spoused(beyonce,jayz).
person(elon).
invspoused(X,Y) :- spoused(Y,X).
spoused(X,Y) :- invspoused(X,Y).
person(X) :- spoused(X,Y).
person(Y) :- spoused(Y,X).
%!mute {person(X)} :- person(X).
%!mute {invspoused(X,Y)} :- invspoused(X,Y).

-spoused(X,Y) :- person(X), person(Y),not spoused(X,Y), not spoused(Y,X).

%-married(X) :- person(X), -spoused(X,Y):person(Y).
-married(X) :- person(X), -spoused(X,Y):person(Y).

%!trace_rule {"% is single, because we proved he is not married",X}.
single(X) :- person(X), -married(X).


%!trace_rule {"% is married",X}.
married(X) :- spoused(X,Y).

%!trace {spoused(X,Y),"% has spoused %",X,Y} :- spoused(X,Y).
%!trace {-spoused(X,Y), "% has not spoused %",X,Y} :- -spoused(X,Y).
%!show_trace {single(X)} :- single(X).
%!show_trace {married(X)} :- married(X).
