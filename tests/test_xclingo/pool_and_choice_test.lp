{switch(s1;s2;s3)}.

%!trace_rule {"bulb is OFF"}
bulb(off) :- not bulb(on).

%!trace_rule {"bulb is ON"}
bulb(on) :- switch(s1), switch(s3).

%!trace {"switch % is enabled",S} switch(S).

%!show_trace bulb(V).
