padre(juan, ana).
abuelo(X, Z) :-
    padre(X, Y),
    padre(Y, Z).
X = Y.
N is 1 + 2 // 3 .
