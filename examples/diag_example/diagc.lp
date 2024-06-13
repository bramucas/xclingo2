exog(break).
exog(surge).
action(Y):-exog(Y).
domain(bulb,ok). domain(bulb,broken).
domain(relay,ok). domain(relay,broken).


%!trace_rule {"The relayline is off at %",T}
c(relayline,off,T) :- h(relay,broken,T), time(T).

%!trace_rule {"The light is off at %",T}
c(light,off,T)     :- h(bulb,broken,T), time(T).

%!trace_rule {"The bulb has been damaged at %",T}
  c(bulb,broken,T) :- o(break,T), time(T),T>0.

%!trace_rule {"The relay has been damaged at %",T}
  c(relay,broken,T) :- o(surge,T), time(T),T>0.

%!trace_rule {"The bulb has been damaged at %",T}
  c(bulb,broken,T) :- o(surge,T), not h(protect,on,T-1), time(T),T>0.

% Something happening actually occurs
  o(A,I) :- obs_o(A,I), time(T),T>0.

% Check that observations hold
  :- obs_h(F,V,J), not h(F,V,J).

%!trace {"Hypothesis: there has been a power surge at %",T} o(surge,T).
%!trace {"Hypothesis: something has broken the bulb at %",T} o(break,T).

% Diagnostic module: generate exogenous actions

% { o(Z,I): exog(Z) } :- time(T),T>0.
  o(Z,T) :- time(T),T>0, exog(Z), not -o(Z,T).
  -o(Z,T) :- time(T),T>0, exog(Z), not o(Z,T).


