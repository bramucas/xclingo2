x(1..9).
y(1..9).
n(1..9).

{sudoku(X,Y,N): n(N)}=1 :- x(X) ,y(Y).

subgrid(X,Y,A,B) :- x(X), x(A), y(Y), y(B),(X-1)/3 == (A-1)/3, (Y-1)/3 == (B-1)/3.

%!trace_rule {"Value % appears twice in column %.", N, Y}.
:- sudoku(X,Y,N), sudoku(A,Y,N), X!=A, X<A.

%!trace_rule {"Value % appears twice in row %", N, X}.
:- sudoku(X,Y,N), sudoku(X,B,N), Y!=B, Y<B.

%!trace_rule {"Value % appears twice in same subgrid", V}.
:- sudoku(X,Y,V), sudoku(A,B,V), subgrid(X,Y,A,B), X != A, Y != B.

% #show sudoku/3.

%!trace {sudoku(X,Y,N), "sudoku(%,%,%)",X,Y,N} :- sudoku(X,Y,N).
