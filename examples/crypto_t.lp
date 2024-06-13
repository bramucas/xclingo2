%%%%%%%% translation %%%%%%%%
% #program base.
#program base.
% #program base.
#program base.
% #const sizeMax = 7.
#const sizeMax = 7.
% key(kab).
_xclingo_sup(1,0,key(kab),()).
% key(kis).
_xclingo_sup(2,0,key(kis),()).
% nonce(ni).
_xclingo_sup(3,0,nonce(ni),()).
% nonce(na).
_xclingo_sup(4,0,nonce(na),()).
% element(X) :- key(X).
_xclingo_sup(5,0,element(X),(X,)) :- _xclingo_model(key(X)).
_xclingo_depends(_xclingo_sup(5,0,element(X),(X,)),key(X)) :- _xclingo_sup(5,0,element(X),(X,)).
% element(X) :- nonce(X).
_xclingo_sup(6,0,element(X),(X,)) :- _xclingo_model(nonce(X)).
_xclingo_depends(_xclingo_sup(6,0,element(X),(X,)),nonce(X)) :- _xclingo_sup(6,0,element(X),(X,)).
% size(X,1) :- element(X).
_xclingo_sup(7,0,size(X,1),(X,)) :- _xclingo_model(element(X)).
_xclingo_depends(_xclingo_sup(7,0,size(X,1),(X,)),element(X)) :- _xclingo_sup(7,0,size(X,1),(X,)).
% size(pair(X,Y),((1+Sx)+Sy)) :- element(X); size(X,Sx); size(Y,Sy); ((Sx+Sy)+1) < sizeMax.
_xclingo_sup(8,0,size(pair(X,Y),((1+Sx)+Sy)),(Sx,X,Sy,Y)) :- _xclingo_model(element(X)); _xclingo_model(size(X,Sx)); _xclingo_model(size(Y,Sy)); ((Sx+Sy)+1) < sizeMax.
_xclingo_depends(_xclingo_sup(8,0,size(pair(X,Y),((1+Sx)+Sy)),(Sx,X,Sy,Y)),(element(X);size(X,Sx);size(Y,Sy))) :- _xclingo_sup(8,0,size(pair(X,Y),((1+Sx)+Sy)),(Sx,X,Sy,Y)).
% size(enc(X,Y),((1+Sx)+Sy)) :- element(X); size(X,Sx); size(Y,Sy); ((Sx+Sy)+1) < sizeMax.
_xclingo_sup(9,0,size(enc(X,Y),((1+Sx)+Sy)),(Sx,X,Sy,Y)) :- _xclingo_model(element(X)); _xclingo_model(size(X,Sx)); _xclingo_model(size(Y,Sy)); ((Sx+Sy)+1) < sizeMax.
_xclingo_depends(_xclingo_sup(9,0,size(enc(X,Y),((1+Sx)+Sy)),(Sx,X,Sy,Y)),(element(X);size(X,Sx);size(Y,Sy))) :- _xclingo_sup(9,0,size(enc(X,Y),((1+Sx)+Sy)),(Sx,X,Sy,Y)).
% iknows(kis).
_xclingo_sup(10,0,iknows(kis),()).
% iknows(ni).
_xclingo_sup(11,0,iknows(ni),()).
% iknows(enc(kab,pair(na,ni))).
_xclingo_sup(12,0,iknows(enc(kab,pair(na,ni))),()).
% iknows(kab).
_xclingo_sup(13,0,iknows(kab),()).
% iknows(pair(X,Y)) :- element(X); iknows(X); iknows(Y); size(pair(X,Y),S); S < sizeMax.
_xclingo_sup(14,0,iknows(pair(X,Y)),(X,S,Y)) :- _xclingo_model(element(X)); _xclingo_model(iknows(X)); _xclingo_model(iknows(Y)); _xclingo_model(size(pair(X,Y),S)); S < sizeMax.
_xclingo_depends(_xclingo_sup(14,0,iknows(pair(X,Y)),(X,S,Y)),(element(X);iknows(X);iknows(Y);size(pair(X,Y),S))) :- _xclingo_sup(14,0,iknows(pair(X,Y)),(X,S,Y)).
% iknows(M) :- iknows(K); iknows(enc(K,M)).
_xclingo_sup(15,0,iknows(M),(K,)) :- _xclingo_model(iknows(K)); _xclingo_model(iknows(enc(K,M))).
_xclingo_depends(_xclingo_sup(15,0,iknows(M),(K,)),(iknows(K);iknows(enc(K,M)))) :- _xclingo_sup(15,0,iknows(M),(K,)).
% iknows(enc(K,M)) :- iknows(K); key(K); iknows(M); size(enc(K,M),S); S < sizeMax.
_xclingo_sup(16,0,iknows(enc(K,M)),(M,K,S)) :- _xclingo_model(iknows(K)); _xclingo_model(key(K)); _xclingo_model(iknows(M)); _xclingo_model(size(enc(K,M),S)); S < sizeMax.
_xclingo_depends(_xclingo_sup(16,0,iknows(enc(K,M)),(M,K,S)),(iknows(K);key(K);iknows(M);size(enc(K,M),S))) :- _xclingo_sup(16,0,iknows(enc(K,M)),(M,K,S)).
% attack :- iknows(enc(kis,pair(na,na))).
_xclingo_sup(17,0,attack,()) :- _xclingo_model(iknows(enc(kis,pair(na,na)))).
_xclingo_depends(_xclingo_sup(17,0,attack,()),iknows(enc(kis,pair(na,na)))) :- _xclingo_sup(17,0,attack,()).
% &show_trace { attack }.
_xclingo_show_trace(attack) :- _xclingo_model(attack).

