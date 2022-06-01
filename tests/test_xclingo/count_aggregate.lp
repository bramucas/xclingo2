numberObjectsbyEntityatTime(N,E,T):- N=#count{O: held_by(O,E,T)}, entity(E),time(T).

time(T):-held_by(O,E,T).
entity(E):-held_by(O,E,T).

held_by(football,mary,0).
held_by(football,mary,0).
held_by(apple,mary,0).
held_by(football,mary,1).
held_by(football,john,1).

%!trace {"% is holding % items at time point %", E,N,T} numberObjectsbyEntityatTime(N,E,T).
%!show_trace numberObjectsbyEntityatTime(N,E,T).