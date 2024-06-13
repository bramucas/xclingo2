plength(1).
% observed initial state
obs_h(s1,open,0).
obs_h(s2,open,0).
obs_h(protect,off,0).
obs_h(relayline,off,0).
obs_h(light,off,0).
obs_h(bulb,ok,0).
obs_h(relay,ok,0).

% observed ation
obs_o(toggle(s1),1).

% Something went wrong
obs_h(light,off,1).
