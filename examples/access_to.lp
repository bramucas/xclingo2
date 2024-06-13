person(a;b;c;d).

has(a, 10).
has(b, 30).
has(c, 10).
has(d, 80).

loves(a, b). 
loves(a, c).
loves(c, b).
loves(d, b).
loves(d, c).
loves(d, a).
loves(b, d).


model(person(a;b;c;d)).
model(has(a, 10)).
model(has(b, 30)).
model(has(c, 10)).
model(has(d, 80)).
model(loves(a, b)).
model(loves(a, c)).
model(loves(c, b)).
model(loves(d, b)).
model(loves(d, c)).
model(loves(d, a)).
model(loves(b, d)).


access_to(P, Money) :-
    Money = #sum{X, Lover: has(Lover, X), loves(Lover, P)},
    person(P).

%%% Traducción:
sup(r1, access_to(P, Money), (Money, P,)) :-
    Money = #sum{X, Lover: model(has(Lover, X)), model(loves(Lover, P))},
    model(person(P)).

aux_agg(r1, agg1, Lover, P, X) :- 
    model(has(Lover, X)), 
    model(loves(Lover, P)).

depends_on(r1, access_to(P, Money), (Money, P,), person(P)) :-
    sup(r1, access_to(P, Money), (Money, P,)).



depends_on(r1, access_to(P, Money), (Money, P,), has(Lover, X)) :-
    % parte estandar
    sup(r1, access_to(P, Money), (Money, P,)),
    % parte agg
    aux_agg(r1, agg1, Lover, P, X).

depends_on(r1, access_to(P, Money), (Money, P,), loves(Lover, P)) :-
    % parte estandar
    sup(r1, access_to(P, Money), (Money, P,)),
    % parte agg
    aux_agg(r1, agg1, Lover, P, X).

#show.
#show depends_on(A, B, C, D) : depends_on(A, B, C, D), B=access_to(P, Money), P=c.
