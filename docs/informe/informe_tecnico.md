# Informe técnico: analizador léxico de un subconjunto de Prolog

## 1. Portada y resumen ejecutivo

| Campo       | Valor                                                                                   |
| ----------- | --------------------------------------------------------------------------------------- |
| Curso       | INFO1148, Teoría de la Computación                                                      |
| Título      | Análisis léxico del lenguaje Prolog: investigación, diseño, implementación y validación |
| Integrantes | [PENDIENTE: completar con los nombres reales antes de entregar]                         |
| Profesor    | Prof. M. Lévano                                                                         |
| Fecha       | 17 de septiembre de 2026                                                                |
| Repositorio | https://github.com/FernandoValdes01/Tarea01TC                                           |

### Resumen ejecutivo

Este informe presenta el análisis, diseño, implementación y validación de un analizador léxico para un subconjunto de Prolog inspirado en la notación de ISO Prolog y SWI-Prolog. El trabajo define formalmente el catálogo de tokens con una expresión regular por categoría, modela las categorías principales con autómatas finitos, muestra la determinización por construcción de subconjuntos y la minimización por refinamiento de particiones sobre un subconjunto representativo, e implementa el lexer en Python con recorrido de izquierda a derecha, máxima coincidencia y prioridades explícitas. El lexer emite tipo, lexema original, línea y columna por token, administra una tabla de lexemas con deduplicación por par tipo y lexema, y reporta seis clases de error con fragmento y posición continuando el análisis. La validación usa una suite de 85 pruebas automatizadas con 26 casos válidos, 22 de prioridad, 16 inválidos y dos archivos completos, con resultado real de 85 aprobadas y cero fallos.

**Palabras clave:** análisis léxico, Prolog, expresiones regulares, autómatas finitos, tabla de lexemas.

## 2. Introducción

El análisis léxico es la primera fase de un compilador: transforma la cadena fuente en una secuencia ordenada de tokens con posición, separando las decisiones regulares (qué formas son válidas) de las decisiones sintácticas (en qué orden pueden aparecer). Un lexer correcto y bien diagnosticado simplifica el parser, produce errores comprensibles y deja evidencia reproducible de cada decisión.

Este informe documenta el subconjunto de Prolog reconocido, su especificación formal, los autómatas que lo modelan, la implementación en Python, la tabla de lexemas, el tratamiento de errores y el plan de pruebas con resultados reales. Cada afirmación remite a su respaldo: sección de la especificación, módulo del código, prueba automatizada o salida de un comando ejecutado.

## 3. Objetivos

El objetivo general es analizar, diseñar, implementar y validar un analizador léxico para un subconjunto definido de Prolog, aplicando alfabetos, lenguajes regulares, expresiones regulares y autómatas finitos, con pruebas reproducibles y diagnósticos verificables.

Los objetivos específicos son: definir formalmente cada categoría con nombre de token, patrón, ejemplos válidos e inválidos y atributo asociado; construir una expresión regular por categoría resolviendo superposiciones con máxima coincidencia y prioridades; modelar las categorías principales con AFN o AFD y presentar un AFD integrado o una estrategia equivalente con estados de aceptación identificados; mostrar la determinización por construcción de subconjuntos y la minimización con justificación de equivalencias sobre un subconjunto representativo; implementar el lexer con posiciones 1-based, tabla de lexemas y seis clases de error recuperables; y validar con al menos 20 pruebas válidas, 8 inválidas, casos de prioridad y dos archivos completos, registrando el resultado real de la suite.

## 4. Alcance del analizador

El analizador reconoce exactamente el catálogo de `docs/informe/01_especificacion_lexica.md`: átomos simples y entre comillas simples, variables nombradas y anónima, enteros y reales sin signo, strings con comillas dobles, los operadores de las seis familias (cláusula, consulta, DCG, unificación y comparación, aritméticos, control), los nueve delimitadores de un carácter y los elementos ignorables (espacios, tabulaciones, saltos de línea y comentarios de línea y de bloque).

Quedan explícitamente fuera del alcance el análisis sintáctico y semántico: no se verifica el orden de los tokens, no se construye un árbol sintáctico, no se comprueba el balance de paréntesis, corchetes o llaves, no se resuelven ámbitos ni variables repetidas, no se implementa unificación, no se evalúan expresiones y no se decide si una secuencia de tokens forma un programa válido. Una `)` aislada es un token `RPAREN` correcto; su posible improcedencia pertenece a una fase posterior.

## 5. Especificación léxica

El contrato completo vive en `docs/informe/01_especificacion_lexica.md` y este capítulo lo resume sin modificarlo. El lexema de cada token es el segmento original de entrada, sin normalización ni conversión de números y sin des-escapar literales. El alfabeto de identificadores es ASCII y cualquier letra, dígito o espacio Unicode fuera de un literal es un carácter no admitido.

| Token                | Patrón Python (`re`)                     | Ejemplos válidos                                                         | Exclusiones                              | Atributo |
| -------------------- | ---------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------- | -------- |
| `ATOM`               | `[a-z][a-z0-9_]*`                        | `padre`, `persona_1`, `isla`                                             | `Padre`, `á`                             | ninguno  |
| `QUOTED_ATOM`        | `'(?:[^\\'\r\n]\|\\[\\'nrt])*'`          | `'Juan Pérez'`, `':-'`, `'it\'s'`                                        | `'sin cierre`, `'a\q'`, `\"` interno     | ninguno  |
| `VARIABLE`           | `(?:[A-Z][A-Za-z0-9_]*\|_[A-Za-z0-9_]+)` | `X`, `Persona`, `_Temporal`, `_1`                                        | `_` solo, `9X`                           | ninguno  |
| `ANONYMOUS_VARIABLE` | `_`                                      | `_`                                                                      | `_X`, `__` (son `VARIABLE`)              | ninguno  |
| `INTEGER`            | `[0-9]+`                                 | `0`, `25`, `0007`                                                        | `-25` (es operador + entero), `5.`, `.5` | ninguno  |
| `REAL`               | `[0-9]+\.[0-9]+`                         | `3.14`, `0.5`, `10.00`                                                   | `5.`, `.5`, `1.2.3`, exponentes          | ninguno  |
| `STRING`             | `"(?:[^\\"\r\n]\|\\[\\"nrt])*"`          | `"hola"`, `"dice \"sí\""`, `"línea\n"`                                   | `"sin cierre`, `"a\q"`, `\'` interno     | ninguno  |
| `OPERATOR`           | unión normativa de la sección 8          | `:-`, `?-`, `-->`, `\==`, `=..`, `//`, `**`, `is`, `mod`, `\+`, `!`, `;` | `:`, `?` y `\` aisladas                  | `family` |
| `LPAREN` … `DOT`     | un carácter cada uno                     | `(`, `)`, `[`, `]`, `{`, `}`, `\|`, `,`, `.`                             | sin validación de balance                | ninguno  |

Las familias de `OPERATOR` son `CLAUSE` (`:-`), `QUERY` (`?-`), `DCG` (`-->`), `UNIFICATION_COMPARISON` (`=`, `\=`, `==`, `\==`, `=..`, `<`, `=<`, `>`, `>=`), `ARITHMETIC` (`+`, `-`, `*`, `/`, `//`, `**`, `is`, `mod`) y `CONTROL` (`\+`, `!`, `;`). La unión normativa implementada en `src/lexer.py` (`OPERATOR_RE`) es idéntica a la del contrato y ordena cada prefijo largo antes que su prefijo corto, con guardas de palabra `(?![A-Za-z0-9_])` para `is` y `mod`.

Las convenciones adoptadas son: los números no tienen signo (`-12` son dos tokens); `INTEGER` y `REAL` no admiten exponentes ni puntos sin dígitos a ambos lados; los escapes válidos son exactamente `\\`, `\'` o `\"` según el delimitador, más `\n`, `\r` y `\t`, y cualquier otra pareja es `INVALID_ESCAPE`; ningún literal admite un salto de línea real en su interior; `%` inicia el comentario de línea hasta antes del salto; `/*` abre un bloque que termina en el primer `*/` sin anidamiento; y las posiciones son 1-based con tabulación de una columna y `\r\n` contado como un único salto.

## 6. Diseño de autómatas

Las figuras usan la convención `estado --símbolo--> estado`, con `(( ))` para aceptación y la etiqueta del token reconocido. Los alfabetos abreviados son `LOWER = [a-z]`, `UPPER = [A-Z]`, `DIGIT = [0-9]` e `ID = [A-Za-z0-9_]`.

Figura 1, AFD de átomos: `q0 --LOWER--> ((q1))` y `q1 --[a-z0-9_]--> q1`. El estado inicial es `q0` y el único estado de aceptación es `q1`, que reconoce `ATOM`. Cualquier otro primer carácter no tiene transición y el dispatcher del lexer lo deriva a otra categoría o a error.

Figura 2, AFD de variables y anónima: `q0 --UPPER--> ((q1))`, `q0 --_--> q2`, `q1 --ID--> q1`, `q2 --ID--> ((q3))` y `q3 --ID--> q3`. El estado `q1` reconoce `VARIABLE` mayúscula, `q3` reconoce `VARIABLE` con guion bajo y el estado `q2` sin continuación se resuelve por la regla prioritaria de `_` aislado como `ANONYMOUS_VARIABLE`, nunca como variable.

Figura 3, AFD de números con trampa de mal formado: `q0 --DIGIT--> ((q1 INTEGER))`, `q1 --DIGIT--> q1`, `q1 --.--TODO q2`, `q2 --DIGIT--> ((q3 REAL))`, `q3 --DIGIT--> q3`, `q0 --.--TODO q4`, `q4 --DIGIT--> q5` y `q5 --[0-9.]--> q5`, con `q2`, `q4` y `q5` no aceptadores. La trampa `q5` captura `.5` y las corridas que el validador reporta como `MALFORMED_NUMBER` (`5.`, `1..2`, `1.2.3`); el lexer implementa este autómata como corrida máxima de `[0-9.]+` seguida de validación exacta contra `INTEGER` o `REAL`.

Figura 4, trie de operadores simbólicos con prefijos comunes: desde `s0`, las ramas `\` llevan a `\=`, `\==` y `\+`; las ramas `=` llevan a `=`, `==`, `=..` y `=<`; `/` lleva a `/`, `//` y al desvío de comentario `/*`; `*` lleva a `*` y `**`; `:` solo continúa a `:-`; `?` solo continúa a `?-`; `-` continúa a `-->`; y `<`, `>`, `+`, `!`, `;` completan las ramas de uno o dos caracteres. Cada nodo de aceptación porta su lexema y su familia; los nodos intermedios sin aceptación (por ejemplo tras `\` o `:`) no emiten token si la entrada termina allí.

Figura 5, AFD de ignorables: espacios y tabulaciones ciclan en consumo de una columna; `\n`, `\r` y `\r\n` producen un salto lógico con reinicio de columna; `%` consume hasta antes del salto; y `/*` entra al cuerpo del bloque, que cicla hasta el primer `*/` o cae al error `UNTERMINATED_BLOCK_COMMENT` al llegar a EOF.

Figura 6, autómata integrado o estrategia equivalente: el lexer implementa un despachador por primera clase de carácter (dígito o punto con dígito siguiente hacia números; comilla hacia literales; letra o guion bajo hacia palabras; símbolo hacia el trie de operadores; espacios, `%` y `/*` hacia ignorables) y en cada posición aplica máxima coincidencia con las prioridades de la sección 8. Esta estrategia es equivalente a la unión de los AFD anteriores con resolución de empates y produce exactamente las mismas particiones de aceptación.

## 7. Determinización y minimización

Para la determinización se tomó el subconjunto representativo de ambigüedad entre operador y comentario con las ramas `/`, `//` y `/* … */`, construido por Thompson como unión de tres ramas con transiciones vacías desde un inicio común. La ε-cerradura del inicio es el conjunto de los tres primeros estados de rama más el inicio, y como ninguna rama intermedia usa transiciones vacías adicionales, cada ε-cerradura posterior es la identidad; se declara así porque el cálculo se hizo y su resultado es trivial, no porque se haya omitido.

| Subconjunto             | Con `/`                    | Con `*` | Con otro            | Aceptación       |
| ----------------------- | -------------------------- | ------- | ------------------- | ---------------- |
| S0 (inicio)             | S1                         | —       | —                   | ninguna          |
| S1 (tras `/`)           | S2                         | S3      | operador `/` simple | `OPERATOR('/')`  |
| S2 (tras `//`)          | —                          | —       | fin de lexema       | `OPERATOR('//')` |
| S3 (cuerpo `/*`)        | S3                         | S4      | S3                  | ninguna          |
| S4 (tras `*` en bloque) | S3 con cierre si sigue `/` | S4      | S3                  | cierre con `*/`  |

La tabla muestra por qué el comentario debe intentarse antes que el operador: desde `S1` el símbolo `*` compromete al autómata con el bloque y abandonar esa rama para emitir `/` más `*` violaría la máxima coincidencia. El lexer respeta este orden al tratar `/*` en la fase de ignorables antes de probar operadores.

Para la minimización se tomó el AFD de números de la Figura 3 con la partición inicial entre aceptadores (`q1` entero, `q3` real) y no aceptadores (`q0`, `q2`, `q4`, `q5`, trampa). El refinamiento separa `q1` de `q3` porque ante `.` transitan a estados de bloques distintos (`q2` frente a trampa), lo que justifica que entero y real nunca se fusionen y que la decisión entre ambos la tome la longitud del lexema. Los estados trampa de número mal formado resultan equivalentes entre sí porque ciclan sobre `[0-9.]` sin aceptar, de modo que se fusionan en una única trampa que el conductor reporta como `MALFORMED_NUMBER` con la corrida completa. Ningún estado aceptador se fusiona con un no aceptador, por lo que el lenguaje reconocido no cambia.

## 8. Reglas de prioridad y máxima coincidencia

En cada posición se elige el candidato válido más largo y solo en empate se aplica la prioridad contractual. La tabla verifica cada regla contra su prueba; `family` abrevia el atributo del operador.

| Entrada            | Candidatos                             | Regla ganadora                        | Resultado                    | Prueba  |
| ------------------ | -------------------------------------- | ------------------------------------- | ---------------------------- | ------- |
| `\==`              | `\==`, `\=`                            | más largo                             | `OPERATOR` unificación       | P01     |
| `=..`              | `=..`, `=`                             | más largo                             | `OPERATOR` unificación       | P02     |
| `==`               | `==`, `=`                              | más largo                             | `OPERATOR` unificación       | P03     |
| `\=`               | `\=`                                   | único                                 | `OPERATOR` unificación       | P04     |
| `:-`               | `:-` frente a `:` inválido             | operador de dos caracteres            | `OPERATOR` cláusula          | P05     |
| `?-`               | `?-` frente a `?` inválido             | operador de dos caracteres            | `OPERATOR` consulta          | P06     |
| `-->`              | `-->`, `-`                             | más largo                             | `OPERATOR` DCG               | P07     |
| `//`               | `//`, `/`                              | más largo                             | `OPERATOR` aritmético        | P08     |
| `**`               | `**`, `*`                              | más largo                             | `OPERATOR` aritmético        | P09     |
| `_`                | anónima frente a variable no aplicable | regla del anónimo                     | `ANONYMOUS_VARIABLE`         | P10     |
| `_Tmp`             | variable completa frente a `_`         | más largo                             | `VARIABLE`                   | P11     |
| `isla`             | `ATOM(4)` frente a prefijo `is`        | más largo y guarda                    | `ATOM`                       | P12     |
| `is`               | `ATOM` y `OPERATOR` de igual longitud  | palabra reservada                     | `OPERATOR` aritmético        | P13     |
| `mod`              | `ATOM` y `OPERATOR` de igual longitud  | palabra reservada                     | `OPERATOR` aritmético        | P14     |
| `modulo`           | `ATOM(6)` frente a prefijo `mod`       | más largo y guarda                    | `ATOM`                       | P15     |
| `1.25`             | `REAL` frente a `INTEGER('1')`         | más largo, `REAL` antes que `INTEGER` | `REAL`                       | P16     |
| `X=Y`              | tres tokens adyacentes                 | el cursor avanza sin separadores      | `X`, `=`, `Y`                | P17     |
| `X\==Y`            | operador largo adyacente               | máxima coincidencia                   | `X`, `\==`, `Y`              | P18     |
| `is(`              | `is` más `(` no continuador            | guarda de palabra                     | `OPERATOR` + `LPAREN`        | P19     |
| `a:-b`             | cláusula adyacente                     | operador de dos caracteres            | `a`, `:-`, `b`               | P20     |
| `12abc`            | `INTEGER('12')` + `ATOM('abc')`        | corrida solo de `[0-9.]`, sin error   | dos tokens, ver nota         | P21     |
| `is_`              | `ATOM(3)` frente a prefijo `is`        | guarda (`_` es continuador)           | `ATOM`                       | P22     |
| `5.`, `.5`, `1..2` | candidato numérico inválido            | detector antes que `DOT`              | `MALFORMED_NUMBER` sin `DOT` | I07–I09 |

La nota de `12abc` es una divergencia declarada con el prompt de pruebas, no con el contrato: la corrida numérica solo incluye dígitos y puntos, de modo que `12` es un entero válido seguido del átomo `abc`. El mínimo de 8 inválidas se cumple con otros 16 casos con error real.

## 9. Diseño e implementación

La arquitectura tiene cuatro módulos con una sola dirección de dependencias: `tokens.py` define `TokenType`, `OperatorFamily`, el mapa `OPERATOR_FAMILY` y el `Token` con posición de inicio y familia opcional; `errors.py` define `ErrorKind` y `LexError` con clase, fragmento, línea, columna y mensaje; `symbol_table.py` implementa `SymbolTable` con deduplicación por par tipo y lexema; `lexer.py` expone `tokenize(source)` y `tokenize_file(path)` y retorna un `LexResult` con tokens en orden, errores acumulados y tabla; y `main.py` ofrece la CLI que imprime cada token como `<TIPO, 'lexema', línea, columna>` más la familia cuando existe, lista los errores con ubicación y, con `--tabla`, vuelca la tabla.

El flujo de datos recorre la entrada de izquierda a derecha con un cursor de índice, línea y columna: primero consume ignorables en bucle (espacios, saltos, comentarios de línea y de bloque), luego prueba el detector numérico cuando hay dígito o punto con dígito siguiente, después los literales con validación de escapes, después `OPERATOR_RE` anclado al cursor, después palabras y anónima, después delimitadores de un carácter y finalmente registra `INVALID_CHARACTER` consumiendo un carácter. Cada token guarda la línea y columna de su primer carácter; la tabulación avanza una columna y `\r\n` cuenta como un único salto.

La salida real del programa válido empieza con `<ATOM, 'padre', 2, 1>`, `<LPAREN, '(', 2, 6>`, `<ATOM, 'juan', 2, 7>` y continúa hasta totalizar 207 tokens, 0 errores y 48 entradas de tabla. La salida del programa con errores termina con los 12 diagnósticos reales listados en la sección 11 y totaliza 69 tokens recuperados. Los comandos reproducibles son `python -m compileall src tests`, `python -m pytest -q`, `python -m src.main tests/corpus/entradas/programa_valido.pl` y `python -m src.main tests/corpus/entradas/programa_con_errores.pl`; en este entorno `python` corresponde a `python3` y la suite se ejecutó con `uv run --with pytest`.

## 10. Tabla de lexemas

Se registran `ATOM`, `QUOTED_ATOM` y `VARIABLE` como identificadores, más `INTEGER`, `REAL` y `STRING` como literales conservables, siempre con el lexema original y sin conversiones. La clave de deduplicación es el par tipo y lexema, de modo que dos apariciones idénticas comparten índice y dos formas textuales distintas nunca se fusionan. Cada token registrable porta su `table_index` puramente léxico.

La variable anónima `_` nunca se registra porque cada aparición es independiente y no un identificador reutilizable. Operadores, delimitadores, espacios y comentarios tampoco se registran. La tabla no guarda alcances, posiciones de uso, unificaciones ni tipos semánticos; la prueba `T08` verifica la deduplicación comparando conjuntos ordenados para no depender del orden interno del diccionario y `T09` verifica que lo no registrable deja la tabla vacía.

## 11. Tratamiento de errores léxicos

Los seis errores contractuales se acumulan sin detener el recorrido y cada diagnóstico incluye clase, fragmento, línea, columna y mensaje útil. El átomo sin cierre descarta hasta antes del salto o hasta EOF (`I01`, `I02`); el string sin cierre hace lo mismo con su delimitador (`I03`, `I04`); el bloque `/*` sin `*/` consume hasta EOF actualizando posiciones y no admite tokens posteriores (`I05`); el carácter no admitido (`@`, `:`, `?`, `\` aislada, `á` y solo espacio, tabulación y saltos como ignorables) consume un carácter y continúa (`I06`, `I13`–`I16`); el número mal formado consume la corrida completa de dígitos y puntos y nunca emite `DOT` para ese fragmento (`I07`–`I10`); y cada escape desconocido registra un `INVALID_ESCAPE` en la barra inversa, consume la pareja y sigue buscando el cierre, de modo que un literal con escapes inválidos no emite token y uno además sin cierre suma el error de cierre (`I11`, `I12`).

La salida real del archivo con errores contiene exactamente estos 12 diagnósticos: `UNTERMINATED_QUOTED_ATOM` en 3:6, `UNTERMINATED_STRING` en 5:6, `INVALID_CHARACTER('@')` en 7:6, `MALFORMED_NUMBER('5.')` en 8:6, `MALFORMED_NUMBER('.5')` en 9:6, `MALFORMED_NUMBER('1..2')` en 10:6, `INVALID_CHARACTER(':')` en 11:5, `INVALID_CHARACTER('?')` en 12:5, `INVALID_CHARACTER('\')` en 13:5, `INVALID_ESCAPE('\q')` en 14:8, `INVALID_ESCAPE('\q')` en 15:8 y `UNTERMINATED_BLOCK_COMMENT` en 17:1 hasta EOF.

## 12. Plan de pruebas y resultados

La suite `tests/test_lexer.py` suma 85 pruebas: 3 del modelo `Token`, 26 válidas `V01`–`V26` con tokens y posiciones exactas, 22 de prioridad `P01`–`P22`, 16 inválidas `I01`–`I16` con clase, fragmento, posición y recuperación, 12 transversales `T01`–`T12` de posiciones, comentarios, escapes, tabla y acumulación, y 6 de archivos `F01`–`F06` incluyendo lectura de los dos programas completos, de los 8 archivos de `validos/` y de los 6 de `invalidos/`, más la verificación del mínimo de corpus. La matriz completa con el resultado real de cada caso vive en `docs/informe/04_matriz_de_pruebas.md`.

El archivo válido produce 207 tokens, 0 errores y 48 entradas, cubriendo los 17 tipos de token y las 6 familias. El archivo con errores produce 69 tokens, 12 errores de las 6 clases en 12 líneas distintas y 28 entradas, con tokens válidos después de cada error recuperable y ningún token después del bloque sin cierre final. El comando ejecutado fue `uv run --with pytest python -m pytest -q` con resultado real `85 passed in 0.08s`; además `python -m compileall src tests` terminó sin errores y `git diff --check` salió limpio.

## 13. Análisis de resultados

La cobertura es total sobre el catálogo: cada tipo de token y cada familia aparece en el corpus válido y en el archivo completo, cada clase de error tiene al menos dos variantes cuando el contrato lo permite (cierre a EOF y antes de salto, escapes en ambos delimitadores, cuatro números mal formados, cuatro caracteres aislados) y cada regla de prioridad tiene su prueba dedicada. Los casos límite confirman que `CRLF` cuenta como un salto, que la tabulación avanza una columna, que los comentarios dentro de literales son contenido, que `-12` son dos tokens y que `)` aislado sigue siendo token.

La principal dificultad fue la interacción entre el punto de fin de cláusula y el detector numérico: una cláusula que termina en número sin espacio (`mod 5.`) es `MALFORMED_NUMBER` por contrato, de modo que los archivos válidos escriben `5 .` con espacio. La segunda fue `12abc`, resuelta como dos tokens según la definición de corrida numérica y declarada como divergencia del prompt, no del contrato. La recuperación quedó demostrada con 69 tokens válidos alrededor de 11 errores recuperables y un último error de bloque que correctamente no deja nada después. El único límite real es documental: `agents.md` y la plantilla de informe no se encontraron en las rutas indicadas, por lo que sus contenidos se marcan como pendientes en lugar de inventarse.

## 14. Conclusiones

El trabajo muestra que un lexer riguroso nace de decisiones contractuales explícitas antes que del código: alfabeto ASCII, números sin signo, escapes cerrados por delimitador, comentarios no anidables y máxima coincidencia con prioridades resolvieron todas las ambigüedades sin casos especiales en la implementación. Los objetivos se cumplieron de forma medible con 85 pruebas aprobadas, cobertura total de categorías y familias, y dos archivos completos que ejercitan el recorrido real.

Las limitaciones reales son que el lexer solo reconoce el subconjunto contratado, que los archivos válidos deben separar con espacio un número del punto final por la regla de número mal formado y que el informe conserva marcadores pendientes para integrantes y plantilla. Como mejoras futuras se proponen modos de salida adicionales (JSON o CSV de tokens), un visualizador de autómatas generado desde las expresiones del código y pruebas de rendimiento sobre archivos grandes, sin ampliar el subconjunto ni entrar en análisis sintáctico.

## 15. Referencias

Las fuentes realmente consultadas, en formato APA 7, se detallan en `docs/informe/referencias.md y comprenden el enunciado de la tarea, la especificación léxica contractual, la matriz de pruebas, el código y el corpus del repositorio, y la documentación oficial de Python (`re`, `pytest`mediante`uv`) usada para implementar y ejecutar la suite. No se inventaron editoriales, autores, URL ni fechas.

## 16. Anexos

Los anexos viven en `docs/informe/anexos.md` e incluyen el enlace real al repositorio, los listados de autómatas completos, las salidas extensas de ambos programas, la evidencia de los comandos de verificación y la lista de comprobación contra la rúbrica con el archivo o prueba que respalda cada dimensión.
