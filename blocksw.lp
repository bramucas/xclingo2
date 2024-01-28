time(0..last). step(1..last). block(1..n).
location(table). location(B):-block(B).

unclear(C,T) :- h(on(B),C,T),C!=table,time(T).
:- o(move(B,_),T), unclear(B,T-1).                   % executability
:- o(move(_,L),T), unclear(L,T-1).                   % executability
:- o(move(B,table),T), h(on(B),table,T-1), step(T).  % executability  
:- g(on(B),L), not h(on(B),L,last).

h(F,V,T) :- h(F,V,T-1), not c(F,T), step(T).         % inertia
c(F,T)   :- h(F,V,T-1),h(F,W,T),V!=W, step(T).       % changes

% Text labels
timetext(0,initially). timetext(last,finally).
changed(on(B),T) :- h(on(B),L,T), h(on(B),L',T-1),L!=L'.
%!trace {h(on(B),L,T), "Block % is % on %",B,Txt,L} :- h(on(B),L,T), timetext(T,Txt).
%!trace {h(on(B),L,T), "Block % is now on % at %",B,L,T} :- h(on(B),L,T), h(on(B),L',T-1), L!=L', T!=last,T!=0.

%!show_trace {h(on(14),V,last)}.
%#show o/2.