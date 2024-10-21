
% I have the obligation not to kill
obl(kill,false).

% CTD: If violate the obligation to kill, I have the obligation to kill gently
obl(kill_gently,true) :- viol(kill,false).

% killing gently counts as killing
h(kill,true) :- h(kill_gently,true).
obl(kill,true) :- obl(kill_gently,true).

%!trace_rule {"I decided to kill"}.
h(kill,true).

