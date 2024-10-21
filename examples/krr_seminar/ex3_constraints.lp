%!trace_rule {"dead from a shot"}
dead :- shoot.

alive.
shoot.

%!trace_rule {"Violated constraint: person cannot be alive and dead"}
:- dead, alive.
