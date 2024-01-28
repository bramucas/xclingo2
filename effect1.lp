action(move(B,table)):- block(B).
action(move(B,C)):- block(B),block(C),B!=C.

1 {o(A,T): action(A) } 1 :- step(T).
h(on(B),L,T) :- o(move(B,L),T).

%!trace {o(move(B,L),T), "We moved block % to % at step %",B,L,T} :- o(move(B,L),T).
