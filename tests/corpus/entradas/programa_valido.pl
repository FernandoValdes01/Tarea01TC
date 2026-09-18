% Hechos
padre(juan, ana).
padre(juan, pedro).

% Regla
abuelo(X, Z) :-
    padre(X, Y),
    padre(Y, Z).

?- abuelo(juan, Quien).

% Listas, llaves, strings y aritmética
lista([ana, pedro | Resto]).
pi(3.14).
datos({ana, 25, "extra"}).
saludo("hola").
mensaje("dice \"si\"\n").
texto('Juan Pérez').
especial(':-').
escape_atom('it\'s').
ruta("ruta\\tmp").
calc(Result) :-
    Temp is 3 + 4 * 2 // 2 ** 2,
    Result is Temp mod 5 .

/* comentario de
   bloque */
regla_dcg(X) --> base(X), X == juan.
cond(A) :- \+ falla(A), !.
opcion(A) :- A = b ; A = c.
comp(X, Y) :- X \= Y, X \== Y, X =.. L, X < Y, X =< Y, X > Y, X >= Y.
anon(_, _Temporal, _1).
