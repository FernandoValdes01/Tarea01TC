% Programa con errores léxicos recuperables
padre(juan, ana).
mal1('sin cierre
sigue_valido(ok).
mal2("sin cierre
otro_valido(1).
mal3 @ resto_valido.
num1(5. ) resto_num.
num2(.5) resto_otro.
num3(1..2) fin_num.
op1(:) fin_op1.
op2(?) fin_op2.
op3(\) fin_op3.
esc1('a\q') cola1.
esc2("a\q") cola2.
ok(final).
/* comentario sin cierre
todo esto se consume hasta EOF
