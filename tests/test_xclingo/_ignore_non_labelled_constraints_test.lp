a.
b:-a.
c:-b.
{d} :- c.

:- d.  % this constraint should be ignored to explain c.

%!show_trace{c}.
