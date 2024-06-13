time(0..L) :- plength(L).

fluent(F) :- domain(F,_X).
domain(s1,open). domain(s1,closed).
domain(s2,open). domain(s2,closed).
domain(light,on). domain(light,off).
domain(protect,on). domain(protect,off).
domain(relayline,on). domain(relayline,off).
domain(bulb,ok). domain(bulb,broken).
domain(relay,ok). domain(relay,broken).

agent(toggle(s1)).
action(Y):-agent(Y).

% Inertia
%chungo2 !trace_rule {"% persited % at %",F,V,T}
h(F,V,T) :- h(F,V,T-1), not -h(F,V,T), time(T),T>0.

%chungo1 !trace {"the value of % is % at %",F,V,T} h(F,V,T).

% any value not holding is -h
-h(F,V,T) :- h(F,W,T), domain(F,V), domain(F,W), W!=V, time(T).

% Direct effects
%!trace_rule {"s1 became closed at %",T}
h(s1,closed,T) :- o(toggle(s1),T), h(s1,open,T-1),   time(T),T>0.
%!trace_rule {"s1 became open at %",T}
h(s1,open,T)   :- o(toggle(s1),T), h(s1,closed,T-1), time(T),T>0.

% Indirect effects
%!trace_rule {"The relay started working at %",T}
    h(relayline,on,T)   :- h(s1,closed,T), h(relayline,off,T-1), not h(relay,broken,T), time(T), T>0.

%!trace_rule {"The relay stopped working at %",T}
    h(relayline,off,T)  :- h(s1,open,T),  h(relayline,on,T-1), time(T), T>0.

%!trace_rule {"s2 became closed at %",T}
h(s2,closed,T)  :- h(relayline,on,T), time(T).

%!trace_rule {"the light was turned on at %",T}
h(light,on,T)    :- h(s2,closed,T), h(s2,open,T-1), not h(bulb,broken,T), time(T), T>0.
%!trace_rule {"the light was turned off at %",T}
h(light,off,T)   :- h(s2,open,T), h(s2,closed,T-1), time(T), T>0.

% Completing the initial state
%   1 {h(F,V,0):domain(F,V)} 1 :- fluent(F).
h(F,V,0) :- domain(F,V), not -h(F,V,0).

%!show_trace h(light,V,T) : plength(T).
%!show_trace h(relayline,V,T): plength(T).

%!trace {"% was initially %",F,V} h(F,V,0).
%!trace {"The agent toggled s1 at %", T} o(toggle(s1), T).

#show o/2.
