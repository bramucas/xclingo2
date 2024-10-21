%!trace_rule {"l1"}
a,b.
%!trace_rule {"l2"}
d :- a, not c.
%!trace_rule {"l3"}
d :- not b.

%!show_trace a.
%!show_trace b.
%!show_trace c.
%!show_trace d.
