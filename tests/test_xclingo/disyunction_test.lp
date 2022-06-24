%!trace_rule {"5"}
p,q.

%!trace_rule {"6"}
q :- p.

%!trace_rule {"7"}
p :- q.

%!show_trace p.
%!show_trace q.
