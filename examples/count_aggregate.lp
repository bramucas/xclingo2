numberObjectsbyEntityatTime(N,E,T):- N=#count{O: held_by(O,E,T)}, entity(E),time(T).

% for this reason it would be cool to have some sort of mute_rule
% time(T):-held_by(O,E,T).
% entity(E):-held_by(O,E,T).

time(0;1).
entity(mary;john;brais).

held_by(football,mary,0).
held_by(football,mary,0).
held_by(apple,mary,0).
held_by(football,mary,1).
held_by(football,john,1).

%!trace {"% is holding % items at time point %", E,N,T} numberObjectsbyEntityatTime(N,E,T).
%!show_trace numberObjectsbyEntityatTime(N,E,T).