% comentario de línea
padre(juan, ana). % comentario final
/* comentario de bloque */
abuelo(X, Z) :-
    padre(X, Y). /* otro bloque */
/* bloque
   multilínea */
?- abuelo(juan, Quien).
