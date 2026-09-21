# Anexos

## Anexo A. Enlace al repositorio

Repositorio real de entrega: https://github.com/FernandoValdes01/Tarea01TC (remoto `origin` verificado con `git remote -v`). El contenido canónico del informe está en `docs/informe/informe_tecnico.md` y el PDF final se genera con el comando documentado en el Anexo C. Integrantes: Fernando Valdes, Juan Muñoz Veloso y Vicente Rivera.

## Anexo B. Autómatas completos

Se reproducen las nueve figuras del capítulo 5 con la misma convención (`--símbolo-->` y etiquetas `/ TOKEN` para los estados aceptores). Los alfabetos son `LOWER = [a-z]`, `UPPER = [A-Z]`, `DIGIT = [0-9]` e `ID = [A-Za-z0-9_]`.

```text
Figura 1 (átomos): q0 --LOWER--> ((q1 ATOM)); q1 --[a-z0-9_]--> q1.
Figura 2 (variables): q0 --UPPER--> ((q1 VARIABLE)); q0 --_--> q2;
  q1 --ID--> q1; q2 --ID--> ((q3 VARIABLE)); q3 --ID--> q3;
  q2 sin continuación = ANONYMOUS_VARIABLE por prioridad.
Figura 3 (números): n0 --DIGIT--> ((nI INTEGER)); nI --DIGIT--> nI;
  nI --.--> nP; nP --DIGIT--> ((nR REAL)); nR --DIGIT--> nR.
  nP no acepta; las corridas rechazadas se diagnostican fuera del AFD como MALFORMED_NUMBER.
Figura 4 (operadores): s0 con ramas \ -> {\=, \==, \+}, = -> {=, ==, =.., =<},
  / -> {/, //, /*}, * -> {*, **}, : -> {:-}, ? -> {?-}, - -> {-->},
  más <, >, +, !, ;; cada aceptación porta lexema y familia.
Figura 5 (ignorables): [ \t] en ciclo de una columna; \n, \r, \r\n un salto;
  % hasta antes del salto; /* ... */ hasta el primer */ o UNTERMINATED_BLOCK_COMMENT.
Figura 6 (integrado): despachador por primera clase + máxima coincidencia +
  prioridades contractuales; equivalente a la unión de las Figuras 1-5.
Figura 7 (AFN representativo): unión ε para =, ==, \= y \==.
Figura 8 (AFD por subconjuntos): A={q0,q1,q4}, B={q2}, C={q3},
  D={q5}, E={q6}, F={q7} y Z=∅.
Figura 9 (AFD mínimo etiquetado): siete estados; las salidas de token distintas
  impiden fusionar los cuatro estados aceptores.
```

Las versiones gráficas de estas figuras están incorporadas al PDF entregable
en las páginas del `Anexo A. Diagramas de autómatas`. Se generan desde las
fuentes de estados y transiciones versionadas con `python tools/build_report_diagrams.py`, evitando
que el informe dependa de una captura manual o de una imagen no reproducible.

## Anexo C. Evidencia de comandos y salidas

Comandos ejecutados desde la raíz del repositorio el 17 de septiembre de 2026:

```bash
python -m compileall -q src tests tools
uv run --with pytest python -m pytest -q
python -m src.main tests/corpus/entradas/programa_valido.pl
python -m src.main tests/corpus/entradas/programa_con_errores.pl
python tools/build_final_report.py
git diff --check
git status --short
```

Resultados reales: `compileall` sin errores, `85 passed`, `git diff --check` limpio. La suite se ejecutó como `uv run --with pytest python -m pytest -q` porque `pytest` no está instalado globalmente.

El programa válido produce 207 tokens, 0 errores y 48 entradas de tabla, con distribución `VARIABLE: 38, ATOM: 34, OPERATOR: 27, LPAREN: 23, RPAREN: 23, COMMA: 22, DOT: 19, INTEGER: 7, STRING: 4, QUOTED_ATOM: 3, LBRACKET: 1, BAR: 1, RBRACKET: 1, REAL: 1, LBRACE: 1, RBRACE: 1, ANONYMOUS_VARIABLE: 1`, y sus primeras líneas son `<ATOM, 'padre', 2, 1>`, `<LPAREN, '(', 2, 6>`, `<ATOM, 'juan', 2, 7>`, `<COMMA, ',', 2, 11>`, `<ATOM, 'ana', 2, 13>`, `<RPAREN, ')', 2, 16>`, `<DOT, '.', 2, 17>`.

El programa con errores produce 69 tokens, 12 errores y 28 entradas, con diagnósticos `UNTERMINATED_QUOTED_ATOM` en 3:6, `UNTERMINATED_STRING` en 5:6, `INVALID_CHARACTER('@')` en 7:6, `MALFORMED_NUMBER('5.')` en 8:6, `MALFORMED_NUMBER('.5')` en 9:6, `MALFORMED_NUMBER('1..2')` en 10:6, `INVALID_CHARACTER(':')` en 11:5, `INVALID_CHARACTER('?')` en 12:5, `INVALID_CHARACTER('\')` en 13:5, `INVALID_ESCAPE('\q')` en 14:8, `INVALID_ESCAPE('\q')` en 15:8 y `UNTERMINATED_BLOCK_COMMENT` en 17:1 hasta EOF.

El PDF final se generó con `python tools/build_final_report.py`, que reutiliza `build_report_diagrams.py`, compone el informe desde Markdown y une el anexo mediante `pdfunite`. El entregable es `docs/informe/Tarea_Fernando_Valdes.pdf`. Se verificó con extracción de texto y conteo de páginas que los operadores `\==`, `=..`, `:-` y `?-` se ven correctamente y que las figuras son legibles.

## Anexo D. Lista de comprobación contra la rúbrica

| Dimensión y puntos                          | Evidencia                                                                                                                                                                                                            | Estado                         |
| ------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| Especificación y expresiones regulares (20) | `docs/informe/01_especificacion_lexica.md` con catálogo, regex y convenciones; informe capítulos 4 y 6; `INTEGER_RE`, `REAL_RE`, clases ASCII y tabla de operadores coherentes en `src/lexer.py` | Demostrado                     |
| Modelado con autómatas (25)                 | Informe capítulo 5 con Figuras 1–9, anexo gráfico en el PDF y proceso único sobre `{=, ==, \=, \==}`: AFN con ε, tabla completa de subconjuntos y minimización del AFD etiquetado | Demostrado                     |
| Implementación del lexer (25)               | `src/` completo con posiciones 1-based, máxima coincidencia y prioridades; salidas reales de ambos programas; comandos de ejecución en el capítulo 9 y el Anexo C                                                    | Demostrado                     |
| Pruebas y errores léxicos (15)              | `tests/test_lexer.py` con 85 pruebas (26 válidas, 22 de prioridad, 16 inválidas, 12 transversales, 6 de archivos), dos archivos completos y `docs/informe/04_matriz_de_pruebas.md` con resultado real                | Demostrado                     |
| Informe, repositorio y presentación (15)    | `docs/informe/informe_tecnico.md`, `referencias.md`, `anexos.md` y PDF final con diagramas; README actualizado; `git remote` real en el Anexo A | Demostrado |
| Pauta y fuentes de verdad                   | Las instrucciones de trabajo fueron proporcionadas externamente; el enunciado y `../teoria-computacion/tareas/Formato Informe Tarea.pdf` fueron localizados y revisados; el PDF final incorpora la estructura, tablas y anexos solicitados | Demostrado |

## Anexo E. Estado final

- No se modificaron los originales del enunciado ni de la plantilla externa.
- Código, pruebas, documentación y PDF final se regeneran con los comandos del Anexo C.
- La suite está en 85 aprobadas y cero fallos.
