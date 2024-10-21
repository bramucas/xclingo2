%!trace_rule {"l1"}
p, q.
%!trace_rule {"l2"}
q :- p.
%!trace_rule {"l3"}
p :- q.

%!show_trace p.
%!show_trace q.
