# xclingo

A tool for explaining and debugging Answer Set Programs.

***IMPORTANT:*** This is a new version of [xclingo](https://github.com/bramucas/xclingo). This version is intended to replace the previous one in the future.

**xclingo** is a clingo-based tool which produces text explanations for the solutions of ASP programs. The original program must be annotated with clingo-friendly annotations and then provided to xclingo. 

All the directives start with a ```%``` character, so they are recognized by clingo as comments and therefore they don't modify the meaning of the original program. In other words: a xclingo-annotated ASP program will still produce the original output when called with clingo. 

## Installation
*Install with python3*

```bash
python3 -m pip install xclingo
```

## Short usage
xclingo must be provided with a maximum number of solutions to be computed for the original program and with the maximum number of explanations to be printed for each solution.

An example (all the solutions and 2 explanations):
```
xclingo -n 0 2 examples/drive.lp
```

Defaults are 1 solution and 1 explanation.

## Example

We have any ASP program:
```
% examples/dont_drive_drunk.lp

person(gabriel;clare).

drive(gabriel).
alcohol(gabriel, 40).
resist(gabriel).

drive(clare).
alcohol(clare, 5).

punish(P) :- drive(P), alcohol(P,A), A>30, person(P).
punish(P) :- resist(P), person(P).

sentence(P, prison) :- punish(P).
sentence(P, innocent) :- person(P), not punish(P).
```

And we write some special comments:
```
% examples/dont_drive_drunk.lp

person(gabriel;clare).

drive(gabriel).
alcohol(gabriel, 40).
resist(gabriel).

drive(clare).
alcohol(clare, 5).

%!trace_rule {"% drove drunk", P}
punish(P) :- drive(P), alcohol(P,A), A>30, person(P).

%!trace_rule {"% resisted to authority", P}
punish(P) :- resist(P), person(P).

%!trace_rule {"% goes to prison",P}
sentence(P, prison) :- punish(P).

%!trace_rule {"% is innocent by default",P}
sentence(P, innocent) :- person(P), not punish(P).

%!trace {"% alcohol's level is %",P,A} alcohol(P,A).
%!trace {"% was drunk",P} alcohol(P,A).

%!show_trace sentence(P,S).
```
We will call those comments *annotations* from now on.

Now we can obtain the answer sets of the (annotated) program with clingo (```clingo -n 0 examples/dont_drive_drunk.lp```):
```
Answer: 1
person(gabriel) person(clare) alcohol(gabriel,40) alcohol(clare,5) drive(gabriel) drive(clare) punish(gabriel) resist(gabriel) sentence(clare,innocent) sentence(gabriel,prison)
SATISFIABLE
```

But also very fashion natural language explanations of with xclingo (```xclingo -n 0 0 examples/dont_drive_drunk.lp```):
```
Answer 1
  *
  |__clare is innocent by default

  *
  |__gabriel goes to prison
  |  |__gabriel drove drunk
  |  |  |__gabriel alcohol's level is 40;gabriel was drunk

  *
  |__gabriel goes to prison
  |  |__gabriel resisted to authority
```

*Note:* for this small example almost all the rules and facts of the program have its own text label (this is, they have been *labelled*). Actually, only labelled rules are used to build the explanations so you can still obtain clear, short explanations even for most complex ASP programs.

## Annotations

### %!trace_rule
Assigns a text to the atom in the head of a rule.
```
%!trace_rule {"% resisted to authority", P}
punish(P) :- resist(P), person(P).
```

### %!trace
Assigns a text to the set of atoms produced by a conditional atom.
```
%!trace {"% alcohol's level is above permitted (%)",P,A} alcohol(P,A) : A>40.
```

### %!show_trace
Selects which atoms should be explained via conditional atoms.
```
%!show_trace sentence(P,S).
```

### %!mute
Mark some atoms as *untraceable*. Therefore, explanations will not include them, nor will atoms cause them.
```
%!mute punish(P) : vip_person(P).
```

## Usage

```
usage: xclingo [-h] [--version] [--only-translate | --only-translate-annotations | --only-explanation-atoms] [--auto-tracing {none,facts,all}] [-n N N] infiles [infiles ...]

Tool for explaining (and debugging) ASP programs

positional arguments:
  infiles               ASP program

optional arguments:
  -h, --help            show this help message and exit
  --version             Prints the version and exists.
  --only-translate      Prints the internal translation and exits.
  --only-translate-annotations
                        Prints the internal translation and exits.
  --only-explanation-atoms
                        Prints the atoms used by the explainer to build the explanations.
  --auto-tracing {none,facts,all}
                        Automatically creates traces for the rules of the program. Default: none.
  -n N N                Number of answer sets and number of desired explanations.
```

## Differences with respect to the previous version

### Choice rules and pooling
They are now supported.
```
n(1..20).
switch(s1;s2;s3;s4).
2{num(N):n(N)}4 :- n(N), N>15.
```
Then can be traced with ```%!trace_rule``` annotations.

### Multiple labels for the same atom

In the [previous version](https://github.com/bramucas/xclingo), multiple labels for the same atom lead to alternative explanations. In this version a single explanation is be produced in which labels are concatenated.

As an example, the following situation:
```
%!trace {"% alcohol's level is above permitted (%)",P,A} alcohol(P,A) : A>40.
%!trace {"% was drunk",P} alcohol(P,A) : A>40.
```

would lead to the following result in the previous version:
```
*
  |__gabriel goes to prison
  |  |__gabriel drove drunk
  |  |  |__gabriel alcohol's level is 40

*
  |__gabriel goes to prison
  |  |__gabriel drove drunk
  |  |  |__gabriel was drunk
```

while the new version will produce:

```
*
  |__gabriel goes to prison
  |  |__gabriel drove drunk
  |  |  |__gabriel alcohol's level is 40;gabriel was drunk
```

###



