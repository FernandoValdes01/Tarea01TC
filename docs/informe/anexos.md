# Anexos

## Anexo A. Enlace al repositorio

Repositorio real de entrega: https://github.com/FernandoValdes01/Tarea01TC (remoto `origin` verificado con `git remote -v`). El informe final en PDF se genera desde `docs/informe/informe_tecnico.md` mediante la fuente LaTeX `docs/informe/informe_tecnico.tex` con el comando documentado en el Anexo C. Integrantes: [PENDIENTE: completar con los nombres reales antes de entregar].

## Anexo B. Autómatas completos

Se reproducen las seis figuras del capítulo 6 con la misma convención (`--símbolo-->`, `(( ))` de aceptación y token reconocido). Los alfabetos son `LOWER = [a-z]`, `UPPER = [A-Z]`, `DIGIT = [0-9]` e `ID = [A-Za-z0-9_]`.

```text
Figura 1 (átomos): q0 --LOWER--> ((q1 ATOM)); q1 --[a-z0-9_]--> q1.
Figura 2 (variables): q0 --UPPER--> ((q1 VARIABLE)); q0 --_--> q2;
  q1 --ID--> q1; q2 --ID--> ((q3 VARIABLE)); q3 --ID--> q3;
  q2 sin continuación = ANONYMOUS_VARIABLE por prioridad.
Figura 3 (números): q0 --DIGIT--> ((q1 INTEGER)); q1 --DIGIT--> q1;
  q1 --.--> q2; q2 --DIGIT--> ((q3 REAL)); q3 --DIGIT--> q3;
  q0 --.--> q4; q4 --DIGIT--> q5; q5 --[0-9.]--> q5 (trampa MALFORMED_NUMBER).
Figura 4 (operadores): s0 con ramas \ -> {\=, \==, \+}, = -> {=, ==, =.., =<},
  / -> {/, //, /*}, * -> {*, **}, : -> {:-}, ? -> {?-}, - -> {-->},
  más <, >, +, !, ;; cada aceptación porta lexema y familia.
Figura 5 (ignorables): [ \t] en ciclo de una columna; \n, \r, \r\n un salto;
  % hasta antes del salto; /* ... */ hasta el primer */ o UNTERMINATED_BLOCK_COMMENT.
Figura 6 (integrado): despachador por primera clase + máxima coincidencia +
  prioridades de la sección 8; equivalente a la unión de las Figuras 1-5.
```

## Anexo C. Evidencia de comandos y salidas

Comandos ejecutados desde la raíz del repositorio el 17 de septiembre de 2026:

```bash
python -m compileall src tests
python -m pytest -q
python -m src.main tests/corpus/entradas/programa_valido.pl
python -m src.main tests/corpus/entradas/programa_con_errores.pl
git diff --check
git status --short
```

Resultados reales: `compileall` sin errores, `85 passed in 0.08s`, `git diff --check` limpio. La suite se ejecutó como `uv run --with pytest python -m pytest -q` porque `pytest` no está instalado globalmente; `uv` resolvió `pytest 9.1.1`.

El programa válido produce 207 tokens, 0 errores y 48 entradas de tabla, con distribución `VARIABLE: 38, ATOM: 34, OPERATOR: 27, LPAREN: 23, RPAREN: 23, COMMA: 22, DOT: 19, INTEGER: 7, STRING: 4, QUOTED_ATOM: 3, LBRACKET: 1, BAR: 1, RBRACKET: 1, REAL: 1, LBRACE: 1, RBRACE: 1, ANONYMOUS_VARIABLE: 1`, y sus primeras líneas son `<ATOM, 'padre', 2, 1>`, `<LPAREN, '(', 2, 6>`, `<ATOM, 'juan', 2, 7>`, `<COMMA, ',', 2, 11>`, `<ATOM, 'ana', 2, 13>`, `<RPAREN, ')', 2, 16>`, `<DOT, '.', 2, 17>`.

El programa con errores produce 69 tokens, 12 errores y 28 entradas, con diagnósticos `UNTERMINATED_QUOTED_ATOM` en 3:6, `UNTERMINATED_STRING` en 5:6, `INVALID_CHARACTER('@')` en 7:6, `MALFORMED_NUMBER('5.')` en 8:6, `MALFORMED_NUMBER('.5')` en 9:6, `MALFORMED_NUMBER('1..2')` en 10:6, `INVALID_CHARACTER(':')` en 11:5, `INVALID_CHARACTER('?')` en 12:5, `INVALID_CHARACTER('\')` en 13:5, `INVALID_ESCAPE('\q')` en 14:8, `INVALID_ESCAPE('\q')` en 15:8 y `UNTERMINATED_BLOCK_COMMENT` en 17:1 hasta EOF.

El PDF se generó con `pdflatex -interaction=nonstopmode informe_tecnico.tex` (dos pasadas) en `docs/informe/` y se copió a `docs/informe/Tarea_JefeGrupo_nombreApellido.pdf`. Se verificó con extracción de texto que los operadores `\==`, `=..`, `:-` y `?-` se ven correctamente, que no quedan marcadores de plantilla y que las tablas son legibles.

## Anexo D. Lista de comprobación contra la rúbrica

| Dimensión y puntos                          | Evidencia                                                                                                                                                                                                            | Estado                         |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Especificación y expresiones regulares (20) | `docs/informe/01_especificacion_lexica.md` con catálogo, una regex por categoría y convenciones; informe capítulos 5–6; `ATOM_RE`, `VARIABLE_RE`, `INTEGER_RE`, `REAL_RE`, `OPERATOR_RE` idénticos en `src/lexer.py` | Demostrado                     |
| Modelado con autómatas (25)                 | Informe capítulos 6–7 con Figuras 1–6, tabla de subconjuntos `/`, `//`, `/*` con ε-cerradura declarada y particiones de minimización del AFD numérico con equivalencias justificadas                                 | Demostrado                     |
| Implementación del lexer (25)               | `src/` completo con posiciones 1-based, máxima coincidencia y prioridades; salidas reales de ambos programas; comandos de ejecución en el capítulo 9 y el Anexo C                                                    | Demostrado                     |
| Pruebas y errores léxicos (15)              | `tests/test_lexer.py` con 85 pruebas (26 válidas, 22 de prioridad, 16 inválidas, 12 transversales, 6 de archivos), dos archivos completos y `docs/informe/04_matriz_de_pruebas.md` con resultado real                | Demostrado                     |
| Informe, repositorio y presentación (15)    | `docs/informe/informe_tecnico.md`, `referencias.md`, `anexos.md` y PDF final sin placeholders salvo integrantes pendientes; README actualizado; `git remote` real en el Anexo A                                      | Demostrado con pendiente menor |
| Requisito no demostrable                    | `agents.md` y `Formato Informe Tarea.pdf` no existen en las rutas indicadas; se declaran como pendientes y no se inventa su contenido                                                                                | Señalado                       |

## Anexo E. Pendientes reales

- Completar los nombres de los integrantes en la portada y renombrar el PDF según el patrón del enunciado cuando los datos estén disponibles.
- Incorporar la plantilla editable si aparece en el repositorio destino, sin modificar sus originales.
- Nada pendiente en código o pruebas: la suite está en 85 aprobadas y cero fallos.
