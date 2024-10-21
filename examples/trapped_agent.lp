#const time=4.
timestep(0..time).
cell((0..4), 0).

trap_at((1,0)).
goal_at((4,0)).

pos((0,0), 0).

1{
    pos((X', Y), T): X'=X+1, cell(X', Y), pos((X, Y), T-1);
    pos((X', Y), T): X'=X-1, cell(X', Y), pos((X, Y), T-1);
    pos((X, Y'), T): Y'=Y+1, cell(X, Y'), pos((X, Y), T-1);
    pos((X, Y'), T): Y'=Y-1, cell(X, Y'), pos((X, Y), T-1)
}1 :- timestep(T), T>0.

%!trace {pos(Pos, T), "Step %: agent moves to %", T, Pos} :- pos(Pos, T).
%!trace {pos(Pos, T), "Trapped!"} :- pos(Pos, T), trap_at(Pos).

%!trace_rule {"Oh no! Trapped", T, TrapPos}.
:- pos(TrapPos, T), trap_at(TrapPos), timestep(T).

%!trace_rule {"In final step % Agent is not at goal %", time, GoalPos}.
:- goal_at(GoalPos), not pos(GoalPos, time).
