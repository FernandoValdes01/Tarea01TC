# Matriz de pruebas del lexer de Prolog

Contrato: `docs/informe/01_especificacion_lexica.md`.
Suite: `tests/test_lexer.py` + corpus en `tests/corpus/`.
Resultado real obtenido con `uv run --with pytest python -m pytest -q`: `85 passed` (sin fallos).
Verificación adicional: `python3 -m compileall src tests` sin errores y `git diff --check` limpio.

Nota sobre `12abc`: el contrato exige consumir la secuencia como un solo `MALFORMED_NUMBER`. La sección 8 de la especificación incorpora esta recuperación para sufijos de identificador y `P21` la verifica. El mínimo de 8 inválidas también se cumple con `I01`–`I16`.

Nota sobre `5.` a fin de cláusula: `mod 5.` es `MALFORMED_NUMBER` según el contrato (sección 7.1). Los archivos válidos usan `5 .` con espacio para separar `INTEGER` y `DOT`.

## Válidos (26 casos, mínimo exigido 20)

| ID  | Archivo o entrada           | Objetivo                          | Resultado esperado                         | Prueba asociada           | Resultado obtenido real   | Estado |
| --- | --------------------------- | --------------------------------- | ------------------------------------------ | ------------------------- | ------------------------- | ------ |
| V01 | `padre`                     | átomo simple                      | `ATOM('padre')` 1:1, sin errores           | `test_corpus_valido[V01]` | 1 token como lo esperado  | OK     |
| V02 | `persona_1`                 | átomo con dígitos y `_`           | `ATOM('persona_1')` 1:1                    | `test_corpus_valido[V02]` | 1 token como lo esperado  | OK     |
| V03 | `Persona`                   | variable con mayúscula            | `VARIABLE('Persona')` 1:1                  | `test_corpus_valido[V03]` | 1 token como lo esperado  | OK     |
| V04 | `_Temporal`                 | variable con prefijo `_`          | `VARIABLE('_Temporal')` 1:1                | `test_corpus_valido[V04]` | 1 token como lo esperado  | OK     |
| V05 | `_`                         | variable anónima                  | `ANONYMOUS_VARIABLE('_')` 1:1              | `test_corpus_valido[V05]` | 1 token como lo esperado  | OK     |
| V06 | `25`                        | entero                            | `INTEGER('25')` 1:1                        | `test_corpus_valido[V06]` | 1 token como lo esperado  | OK     |
| V07 | `3.14`                      | real                              | `REAL('3.14')` 1:1                         | `test_corpus_valido[V07]` | 1 token como lo esperado  | OK     |
| V08 | `'Juan Pérez'`              | átomo entre comillas con espacio  | `QUOTED_ATOM` 1:1                          | `test_corpus_valido[V08]` | 1 token como lo esperado  | OK     |
| V09 | `':-'`                      | átomo entre comillas con especial | `QUOTED_ATOM("':-'")` 1:1                  | `test_corpus_valido[V09]` | 1 token como lo esperado  | OK     |
| V10 | `"línea\n"`                 | string con escape `\n`            | `STRING` 1:1                               | `test_corpus_valido[V10]` | 1 token como lo esperado  | OK     |
| V11 | `:- ?- -->`                 | cláusula, consulta y DCG          | 3 `OPERATOR` en 1:1, 1:4, 1:7 con familias | `test_corpus_valido[V11]` | 3 tokens como lo esperado | OK     |
| V12 | `= \= == \== =.. < =< > >=` | unificación y comparación         | 9 `OPERATOR` con posiciones exactas        | `test_corpus_valido[V12]` | 9 tokens como lo esperado | OK     |
| V13 | `+ - * / // ** is mod`      | aritméticos                       | 8 `OPERATOR` familia `ARITHMETIC`          | `test_corpus_valido[V13]` | 8 tokens como lo esperado | OK     |
| V14 | `\+ ! ;`                    | control                           | 3 `OPERATOR` familia `CONTROL`             | `test_corpus_valido[V14]` | 3 tokens como lo esperado | OK     |
| V15 | `( )`                       | paréntesis                        | `LPAREN` 1:1, `RPAREN` 1:3                 | `test_corpus_valido[V15]` | 2 tokens como lo esperado | OK     |
| V16 | `[ ]`                       | corchetes                         | `LBRACKET` 1:1, `RBRACKET` 1:3             | `test_corpus_valido[V16]` | 2 tokens como lo esperado | OK     |
| V17 | `{ }`                       | llaves                            | `LBRACE` 1:1, `RBRACE` 1:3                 | `test_corpus_valido[V17]` | 2 tokens como lo esperado | OK     |
| V18 | `\|`                        | barra vertical                    | `BAR` 1:1                                  | `test_corpus_valido[V18]` | 1 token como lo esperado  | OK     |
| V19 | `, .`                       | coma y punto                      | `COMMA` 1:1, `DOT` 1:3                     | `test_corpus_valido[V19]` | 2 tokens como lo esperado | OK     |
| V20 | `% comentario\n  padre`     | comentario de línea + espacios    | `ATOM('padre')` 2:3                        | `test_corpus_valido[V20]` | 1 token como lo esperado  | OK     |
| V21 | `/* bloque */ padre`        | comentario de bloque              | `ATOM('padre')` 1:14                       | `test_corpus_valido[V21]` | 1 token como lo esperado  | OK     |
| V22 | ` \t\n\r\nX`                | espacios, tab y `CRLF` único      | `VARIABLE('X')` 3:1                        | `test_corpus_valido[V22]` | 1 token como lo esperado  | OK     |
| V23 | `padre(juan, ana).`         | hecho con posiciones              | 7 tokens con columnas exactas              | `test_corpus_valido[V23]` | 7 tokens como lo esperado | OK     |
| V24 | `"dice \"si\""`             | string con `\"`                   | `STRING` 1:1                               | `test_corpus_valido[V24]` | 1 token como lo esperado  | OK     |
| V25 | `'it\'s'`                   | átomo con `\'`                    | `QUOTED_ATOM` 1:1                          | `test_corpus_valido[V25]` | 1 token como lo esperado  | OK     |
| V26 | `[X, Y \| Z]`               | lista con barra y coma            | 7 tokens con posiciones                    | `test_corpus_valido[V26]` | 7 tokens como lo esperado | OK     |

## Prioridad y máxima coincidencia

| ID  | Archivo o entrada | Objetivo                                                        | Resultado esperado                           | Prueba asociada                             | Resultado obtenido real              | Estado |
| --- | ----------------- | --------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------- | ------------------------------------ | ------ |
| P01 | `\==`             | un operador completo                                            | `OPERATOR('\==')`                            | `test_prioridad_y_maxima_coincidencia[P01]` | 1 token como lo esperado             | OK     |
| P02 | `=..`             | un operador completo                                            | `OPERATOR('=..')`                            | `test_prioridad_y_maxima_coincidencia[P02]` | 1 token como lo esperado             | OK     |
| P03 | `==`              | un operador completo                                            | `OPERATOR('==')`                             | `test_prioridad_y_maxima_coincidencia[P03]` | 1 token como lo esperado             | OK     |
| P04 | `\=`              | un operador completo                                            | `OPERATOR('\=')`                             | `test_prioridad_y_maxima_coincidencia[P04]` | 1 token como lo esperado             | OK     |
| P05 | `:-`              | cláusula                                                        | `OPERATOR(':-', CLAUSE)`                     | `test_prioridad_y_maxima_coincidencia[P05]` | 1 token como lo esperado             | OK     |
| P06 | `?-`              | consulta                                                        | `OPERATOR('?-', QUERY)`                      | `test_prioridad_y_maxima_coincidencia[P06]` | 1 token como lo esperado             | OK     |
| P07 | `-->`             | DCG                                                             | `OPERATOR('-->', DCG)`                       | `test_prioridad_y_maxima_coincidencia[P07]` | 1 token como lo esperado             | OK     |
| P08 | `//`              | completo, no dos `/`                                            | `OPERATOR('//')`                             | `test_prioridad_y_maxima_coincidencia[P08]` | 1 token como lo esperado             | OK     |
| P09 | `**`              | completo, no dos `*`                                            | `OPERATOR('**')`                             | `test_prioridad_y_maxima_coincidencia[P09]` | 1 token como lo esperado             | OK     |
| P10 | `_`               | anónima                                                         | `ANONYMOUS_VARIABLE`                         | `test_prioridad_y_maxima_coincidencia[P10]` | 1 token como lo esperado             | OK     |
| P11 | `_Tmp`            | variable                                                        | `VARIABLE('_Tmp')`                           | `test_prioridad_y_maxima_coincidencia[P11]` | 1 token como lo esperado             | OK     |
| P12 | `isla`            | un `ATOM`                                                       | `ATOM('isla')`                               | `test_prioridad_y_maxima_coincidencia[P12]` | 1 token como lo esperado             | OK     |
| P13 | `is`              | `OPERATOR` aritmético                                           | `OPERATOR('is', ARITHMETIC)`                 | `test_prioridad_y_maxima_coincidencia[P13]` | 1 token como lo esperado             | OK     |
| P14 | `mod`             | `OPERATOR` aritmético                                           | `OPERATOR('mod', ARITHMETIC)`                | `test_prioridad_y_maxima_coincidencia[P14]` | 1 token como lo esperado             | OK     |
| P15 | `modulo`          | un `ATOM`                                                       | `ATOM('modulo')`                             | `test_prioridad_y_maxima_coincidencia[P15]` | 1 token como lo esperado             | OK     |
| P16 | `1.25`            | `REAL`                                                          | `REAL('1.25')`                               | `test_prioridad_y_maxima_coincidencia[P16]` | 1 token como lo esperado             | OK     |
| P17 | `X=Y`             | adyacentes sin espacios                                         | `VARIABLE`, `=`, `VARIABLE` en 1:1, 1:2, 1:3 | `test_prioridad_y_maxima_coincidencia[P17]` | 3 tokens como lo esperado            | OK     |
| P18 | `X\==Y`           | largo adyacente                                                 | `X` 1:1, `\==` 1:2, `Y` 1:5                  | `test_prioridad_y_maxima_coincidencia[P18]` | 3 tokens como lo esperado            | OK     |
| P19 | `is(`             | `is` + paréntesis                                               | `OPERATOR('is')` 1:1, `LPAREN` 1:3           | `test_prioridad_y_maxima_coincidencia[P19]` | 2 tokens como lo esperado            | OK     |
| P20 | `a:-b`            | cláusula adyacente                                              | `a` 1:1, `:-` 1:2, `b` 1:4                   | `test_prioridad_y_maxima_coincidencia[P20]` | 3 tokens como lo esperado            | OK     |
| P21 | `12abc`           | detector de número mal formado                               | `MALFORMED_NUMBER('12abc')` 1:1, sin tokens | `test_prioridad_y_maxima_coincidencia[P21]` | 1 error como lo esperado             | OK     |
| P22 | `is_`             | `ATOM` por guarda                                               | `ATOM('is_')`                                | `test_prioridad_y_maxima_coincidencia[P22]` | 1 token como lo esperado             | OK     |

## Inválidos (16 casos, mínimo exigido 8)

| ID  | Archivo o entrada      | Objetivo                           | Resultado esperado                                 | Prueba asociada                                           | Resultado obtenido real             | Estado |
| --- | ---------------------- | ---------------------------------- | -------------------------------------------------- | --------------------------------------------------------- | ----------------------------------- | ------ |
| I01 | `'Juan`                | átomo sin cierre a EOF             | `UNTERMINATED_QUOTED_ATOM` 1:1, 0 tokens           | `test_invalido_I01_atom_sin_cierre_eof`                   | 1 error como lo esperado            | OK     |
| I02 | `'sin cierre\npadre.`  | sin cierre con recuperación        | error 1:1 + `padre` 2:1, `.` 2:6                   | `test_invalido_I02_atom_sin_cierre_con_recuperacion`      | 1 error y 2 tokens como lo esperado | OK     |
| I03 | `"Juan`                | string sin cierre a EOF            | `UNTERMINATED_STRING` 1:1                          | `test_invalido_I03_string_sin_cierre`                     | 1 error como lo esperado            | OK     |
| I04 | `"sin cierre\nX.`      | string sin cierre con recuperación | error 1:1 + `X` 2:1, `.` 2:2                       | `test_invalido_I04_string_sin_cierre_con_recuperacion`    | 1 error y 2 tokens como lo esperado | OK     |
| I05 | `padre. /* sin cierre` | bloque sin cierre a EOF            | `UNTERMINATED_BLOCK_COMMENT` 1:8, 2 tokens previos | `test_invalido_I05_bloque_sin_cierre_consume_eof`         | 1 error como lo esperado            | OK     |
| I06 | `@ padre`              | carácter no admitido               | `INVALID_CHARACTER('@')` 1:1 + `padre` 1:3         | `test_invalido_I06_caracter_no_admitido_con_recuperacion` | 1 error y 1 token como lo esperado  | OK     |
| I07 | `5. padre`             | número `5.` sin `DOT`              | `MALFORMED_NUMBER('5.')` 1:1 + `padre` 1:4         | `test_invalido_I07_numero_5_punto`                        | 1 error como lo esperado            | OK     |
| I08 | `.5`                   | número `.5`                        | `MALFORMED_NUMBER('.5')` 1:1                       | `test_invalido_I08_numero_punto_5`                        | 1 error como lo esperado            | OK     |
| I09 | `1..2`                 | corrida `1..2`                     | `MALFORMED_NUMBER('1..2')` 1:1                     | `test_invalido_I09_numero_1_punto_punto_2`                | 1 error como lo esperado            | OK     |
| I10 | `1.2.3`                | variante con dos puntos            | `MALFORMED_NUMBER('1.2.3')` 1:1                    | `test_invalido_I10_numero_1_punto_2_punto_3`              | 1 error como lo esperado            | OK     |
| I11 | `'a\q'`                | escape desconocido en átomo        | `INVALID_ESCAPE('\q')` 1:3, 0 tokens               | `test_invalido_I11_escape_desconocido_en_atom`            | 1 error como lo esperado            | OK     |
| I12 | `"a\'b"`               | `\'` inválido en string            | `INVALID_ESCAPE` 1:3, 0 tokens                     | `test_invalido_I12_escape_desconocido_en_string`          | 1 error como lo esperado            | OK     |
| I13 | `: padre`              | `:` sin `-`                        | `INVALID_CHARACTER(':')` 1:1 + `padre` 1:3         | `test_invalido_I13_dos_puntos_sin_guion`                  | 1 error como lo esperado            | OK     |
| I14 | `?`                    | `?` sin `-`                        | `INVALID_CHARACTER('?')` 1:1                       | `test_invalido_I14_interrogacion_sin_guion`               | 1 error como lo esperado            | OK     |
| I15 | `\ X`                  | `\` aislada                        | `INVALID_CHARACTER('\')` 1:1 + `X` 1:3             | `test_invalido_I15_barra_aislada`                         | 1 error como lo esperado            | OK     |
| I16 | `á`                    | Unicode fuera de literal           | `INVALID_CHARACTER('á')` 1:1                       | `test_invalido_I16_unicode_fuera_de_literal`              | 1 error como lo esperado            | OK     |

## Transversales y archivos

| ID  | Archivo o entrada                  | Objetivo                     | Resultado esperado                      | Prueba asociada                                                | Resultado obtenido real                          | Estado |
| --- | ---------------------------------- | ---------------------------- | --------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------ | ------ |
| T01 | `a\nb\rc\r\nd`                     | multilínea con `CRLF` único  | 4 átomos en 1:1, 2:1, 3:1, 4:1          | `test_posiciones_multilinea_y_columnas`                        | 4 tokens como lo esperado                        | OK     |
| T02 | `a\tb`                             | tab como 1 columna           | `a` 1:1, `b` 1:3                        | `test_tab_solo_avanza_una_columna`                             | 2 tokens como lo esperado                        | OK     |
| T03 | `% hola\nX`                        | línea ignora y posiciona     | `X` 2:1                                 | `test_comentario_linea_no_genera_token`                        | 1 token como lo esperado                         | OK     |
| T04 | `/* a\nb */X`                      | bloque multilínea            | `X` 2:5                                 | `test_comentario_bloque_multilinea_actualiza_posicion`         | 1 token como lo esperado                         | OK     |
| T05 | `'% x' "/* y */"`                  | comentario dentro de literal | 2 literales, 0 errores                  | `test_comentario_dentro_de_literal_es_contenido`               | 2 tokens como lo esperado                        | OK     |
| T06 | 6 literales                        | escapes por tipo             | lexema conservado                       | `test_escapes_validos_por_tipo_de_literal`                     | 6/6 sin errores                                  | OK     |
| T07 | `'a\"b'`, `"a\'b"`                 | escapes cruzados inválidos   | 1 `INVALID_ESCAPE` cada uno             | `test_escape_invalido_cruzado_por_delimitador`                 | 2 errores como lo esperado                       | OK     |
| T08 | `padre padre Persona padre 25 25`  | deduplicación `(tipo, lexema)` | 3 entradas, índices iguales             | `test_tabla_dedup_por_tipo_y_lexema`                           | 3 entradas como lo esperado                      | OK     |
| T09 | `_ :- (`                           | no registrables              | tabla vacía                             | `test_anonima_no_se_registra_y_operadores_no_se_registran`     | 0 entradas como lo esperado                      | OK     |
| T10 | `@\n5.\n: ok.`                     | acumulación y recuperación   | 3 errores líneas 1,2,3 + `ok` `.`       | `test_errores_se_acumulan_y_se_recupera`                       | 3 errores como lo esperado                       | OK     |
| T11 | `)`                                | sin balance sintáctico       | `RPAREN` 1:1                            | `test_paren_aislado_sigue_siendo_token`                        | 1 token como lo esperado                         | OK     |
| T12 | `-12`                              | signo como operador          | `-` 1:1 + `12` 1:2                      | `test_menos_doce_es_operador_mas_entero`                       | 2 tokens como lo esperado                        | OK     |
| F01 | `entradas/programa_valido.pl`      | archivo válido completo      | 0 errores, 17 tipos y 6 familias        | `test_archivo_valido_sin_errores_y_con_categorias`             | 0 errores, cobertura completa                    | OK     |
| F02 | `entradas/programa_con_errores.pl` | archivo con errores          | >=8 errores, recuperación, bloque final | `test_archivo_con_errores_recupera_y_bloque_final_no_recupera` | 12 errores en 12 líneas, recuperación verificada | OK     |
| F03 | `corpus/validos/*.pl`              | 8 archivos válidos           | 0 errores cada uno                      | `test_corpus_validos_en_disco_sin_errores`                     | 8/8 sin errores                                  | OK     |
| F04 | `corpus/invalidos/*.pl`            | 6 archivos inválidos         | >=1 error cada uno                      | `test_corpus_invalidos_en_disco_con_error`                     | 6/6 con error                                    | OK     |
| F05 | conteo                             | mínimo de corpus             | >=20 V, >=14 P, >=8 I, 2 archivos       | `test_minimo_de_corpus`                                        | 26 V, 22 P, 16 I, 2 archivos                     | OK     |

## Comandos ejecutados

```bash
python3 -m compileall src tests
uv run --with pytest python -m pytest -q
git diff --check
```

Salida real:

```text
85 passed
```

`compileall` lista los archivos sin errores y `git diff --check` sale con código 0.
