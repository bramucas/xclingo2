%%% actions

% 1{move(roomA); move(roomB)}1.
move(roomB).

%!trace {move(D), "The player moved to %", D} :- move(D).

player_position(P) :- move(P).

%%%%%%%%%%%%%%%%%%%%%%%%%

trap(roomA, cage).
trap(roomB, trap_door).
trap(hole, water). 

%%%%%%%%%%%%%%%%%%%%%%%%%

triggered(Trap, Position) :- trap(Position, Trap), player_position(Position).

%!trace {triggered(Trap, Position), "Trap triggered at % !! (%)", Position, Trap} :- triggered(Trap, Position).

player_condition(caged) :- triggered(cage, Position).

move(hole) :- triggered(trap_door, Position).
player_condition(drawn) :- triggered(water, Position).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

gameover :- player_condition(caged).
gameover :- player_condition(drawn).

%!trace_rule {"Game over"}.
:- gameover.

%!trace {player_condition(Condition), "Player is %", Condition} :- player_condition(Condition).
