cause(IDCause, ToExplainAtom, root, root) :- f(IDCause, ToExplainAtom, _), to_explain(ToExplainAtom).
cause(IDCause, Cause, Caused, IDCaused) :- f(IDCause, Cause, _), inbody((Cause, Body)), f(IDCaused, Caused, Body).
cause(true, true,  Caused, ID) :- f(ID, Caused, empty).