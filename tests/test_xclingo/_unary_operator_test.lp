%%% thresholds
class(1,I, 100) :- le(I,1,50), le(I,5,18), le(I,9,-164).
class(0,I, 97) :- le(I,1,50), le(I,5,18), gt(I,9,-164).
class(1,I, 100) :- gt(I,1,50), le(I,5,-4).
class(0,I, 100) :- gt(I,1,50), between(I,5,-4,18).
class(0,I, 80) :- le(I,0,-64), between(I,5,18,140).
class(1,I, 83) :- le(I,0,-64), gt(I,5,140).
class(0,I, 100) :- gt(I,0,-64), gt(I,5,18), le(I,6,-183).
class(1,I, 100) :- gt(I,0,-64), gt(I,5,18), gt(I,6,-183).
%%% paths
thres(18).
thres(50).
thres(140).%
thres(-164).%
thres(-4).%
thres(-64).%
%%% base
gt(I, F, T) :- value(I, F, V), V>T, thres(T).
le(I, F, T) :- value(I, F, V), V<=T, thres(T).
between(I, F, Min, Max) :- value(I, F, V), V>Min, thres(Min), V<=Max, thres(Max).

prediction(I) :- class(C,I,P).

%!show_trace {prediction(I)}.
%
%%% feature names
feature_name(0,"f0").
feature_name(1,"f1").
feature_name(2,"f2").
feature_name(3,"f3").
feature_name(4,"f4").
feature_name(5,"f5").
feature_name(6,"f6").
feature_name(7,"f7").
feature_name(8,"f8").
feature_name(9,"f9").

% instance
value(1,1,0).
value(1,5,0).
value(1,9,0).