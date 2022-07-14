numberObjectsbyEntityatTime(N,E,T):- N=#count{O: held_by(O,E,T)}, entity(E),time(T).

%!mute_body.
time(T) :- held_by(O,E,T).
%!mute_body.
entity(E) :- held_by(O,E,T).

held_by(football,mary,0). % this is repeated
held_by(football,mary,0).
held_by(apple,mary,0).
held_by(football,mary,1).
held_by(football,john,1).

%!trace {numberObjectsbyEntityatTime(N,E,T), "% is holding % items at time point %", E,N,T} :- numberObjectsbyEntityatTime(N,E,T).
%!trace {held_by(O,E,T), "% holding % at %", E, O, T} :- held_by(O,E,T).
%!show_trace {numberObjectsbyEntityatTime(N,E,T)} :- numberObjectsbyEntityatTime(N,E,T).