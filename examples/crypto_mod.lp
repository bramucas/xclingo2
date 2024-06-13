

#const sizeMax=7.

key(kab).
key(kis).

nonce(ni).
nonce(na).

element(X):- key(X).
element(X):- nonce(X).

size(X,1) :- element(X).
size(pair(X,Y),1+Sx+Sy):- element(X), size(X,Sx), size(Y,Sy), Sx+Sy+1<sizeMax.
size(enc(X,Y),1+Sx+Sy):- element(X), size(X,Sx), size(Y,Sy), Sx+Sy+1<sizeMax.

%Initial knowledge
iknows(kis).
iknows(ni).
iknows(enc(kab,pair(na,ni))).
iknows(kab).

% Pairing
%!trace_rule {"% and % -> pair(%,%)",X,Y,X,Y}.
iknows(pair(X,Y)) :- element(X), iknows(X), iknows(Y), size(pair(X,Y),S), S<sizeMax.

% Unpairing
%!trace_rule {"pair(%,%) -> %",X,Y,X}.
%iknows(X) :- iknows(pair(X,Y)).
%!trace_rule {"pair(%,%) -> %",X,Y,Y}.
%iknows(Y) :- iknows(pair(X,Y)).

% Decyphering
%!trace_rule {"enc(%,%) and % -> %",K,M,K,M}.
iknows(M) :- iknows(K), iknows(enc(K,M)).

% Cyphering
%!trace_rule {"% and % -> enc(%,%)",K,M,K,M}.
iknows(enc(K,M)) :- iknows(K), key(K), iknows(M), size(enc(K,M),S), S<sizeMax.

attack:- iknows(enc(kis,pair(na,na))).
%#show attack/0. %Fast with clingo

%!show_trace {attack}.