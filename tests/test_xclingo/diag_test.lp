plength(8).

%initial state
h(light, off, 0).
h(protect, on, 0).
h(relayline, off, 0).
h(s1, open, 0).
h(s2, open, 0).

% actions
o(toggle(s1), 2).
o(toggle(s1), 5).

time(0..L) :- plength(L).

fluent(F) :- domain(F,_X).
domain(s1,open). domain(s1,closed).
domain(s2,open). domain(s2,closed).
domain(light,on). domain(light,off).
domain(protect,on). domain(protect,off).
domain(relayline,on). domain(relayline,off).

agent(toggle(s1)).
action(Y):-agent(Y).

c(F,T)   :- c(F,V,T).
h(F,V,T) :- c(F,V,T).

% Direct effects
%!trace_rule {"s1 was closed at %",T}
c(s1,closed,T) :- o(toggle(s1),T), h(s1,open,T-1), time(T),T>0.

%!trace_rule {"s1 was open at %",T}
c(s1,open,T) :- o(toggle(s1),T), h(s1,closed,T-1), time(T),T>0.

% try using negation not h(s1,open,T-1)

% Indirect effects
%!trace_rule {"The relay started working at %",T}
    c(relayline,on,T)   :- c(s1,closed,T), not h(relay,broken,T), time(T).

%!trace_rule {"The relay stopped working at %",T}
    c(relayline,off,T)  :- c(s1,open,T), time(T).

%!trace_rule {"s2 was closed at %",T}
c(s2,closed,T)  :- c(relayline,on,T), time(T).

%!trace_rule {"The light was turned on at %",T}
c(light,on,T)    :- c(s2,closed,T), not h(bulb,broken,T), time(T).
%!trace_rule {"The light was turned off at %",T}
c(light,off,T)   :- c(s2,open,T), time(T).

% Inertia
%%%%% !trace_rule {"% persited % at %",F,V,T}
h(F,V,T) :- h(F,V,T-1), not c(F,T), time(T),T>0.



% Completing the initial state
%   1 {h(F,V,0):domain(F,V)} 1 :- fluent(F).
h(F,V,0) :- domain(F,V), not -h(F,V,0).
% any value not holding is -h
-h(F,V,0) :- h(F,W,0), domain(F,V), W!=V.


%!show_trace h(light,V,T) : plength(T).
%!show_trace h(relayline,V,T): plength(T).


%!trace {"% was initially %",F,V} h(F,V,0).
%!trace {"The agent toggled s1 at %", T} o(toggle(s1), T).

#show o/2.
#show h/3.
