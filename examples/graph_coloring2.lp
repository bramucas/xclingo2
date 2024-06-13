e(1,2). e(3,2). e(1,3). e(3,4). e(2,5). e(4,5).
color(blue;red).
node(X;Y) :- e(X,Y).

1{picked(X,C): color(C)}1 :- node(X).

_same_color(1, (X,Y,C)) :- e(X,Y), picked(X,C), picked(Y,C).

#show _same_color/2.


#minimize{1,ID,Vars: _same_color(ID,Vars)}.

