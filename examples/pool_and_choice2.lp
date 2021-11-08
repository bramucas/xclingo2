{switch(1..3)}.

%!trace_rule {"bulb is OFF"}
bulb(off) :- not bulb(on).

%!trace_rule {"bulb is ON"}
bulb(on) :- switch(1), switch(3).

%!trace {"switch % is enabled",S} switch(S).

%!show_trace bulb(V).
