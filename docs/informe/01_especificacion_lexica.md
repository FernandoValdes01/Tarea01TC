# Especificación léxica contractual del subconjunto de Prolog

**Estado:** contrato para una implementación posterior. Este documento no implementa el
lexer, no define una gramática de cláusulas y no realiza análisis sintáctico ni semántico.

## 1. Alcance y objetivo

El analizador léxico recibirá una cadena fuente y la recorrerá de izquierda a derecha.
En cada posición reconocerá el lexema válido más largo que comience allí, emitirá un
token con su lexema y posición de inicio, o registrará un error léxico recuperable. Los
tokens conservarán el orden de aparición.

El subconjunto cubierto es exactamente el catálogo de este documento: átomos,
variables, números enteros y reales, cadenas, operadores seleccionados y delimitadores.
También se reconocen espacios y comentarios como elementos ignorables.

Queda fuera de este contrato:

- verificar el orden o la estructura de una cláusula o consulta;
- comprobar paréntesis, corchetes o llaves balanceados;
- determinar aridad, precedencia o asociatividad de operadores;
- resolver ámbitos, variables repetidas, unificación o cualquier otra propiedad
  semántica;
- convertir números o des-escapar literales para atribuirles significado;
- decidir si una secuencia de tokens es un programa Prolog válido.

Una `)` aislada, por ejemplo, sigue siendo un `RPAREN`: su posible improcedencia es
sintáctica, no léxica.

## 2. Decisiones contractuales

Se adoptan las convenciones solicitadas para eliminar decisiones implícitas en la etapa
de implementación. Las fuentes consultadas permiten estas decisiones: el enunciado
deja abierta la política de signos y de escapes, y el presente contrato la fija.

| Nº | Decisión | Consecuencia observable |
|---:|---|---|
| 1 | El alfabeto de identificadores es ASCII: `A-Z`, `a-z`, `0-9` y `_`. | Una letra, dígito o espacio Unicode fuera de un literal es un carácter no admitido; no extiende una palabra ASCII. |
| 2 | Un átomo no entrecomillado es `[a-z][a-z0-9_]*`. | Comienza siempre con minúscula ASCII. |
| 3 | Una variable es `[A-Z][A-Za-z0-9_]*` o `_[A-Za-z0-9_]+`. | `_` requiere tratamiento separado como variable anónima. |
| 4 | `_` aislado es `ANONYMOUS_VARIABLE`. | Se conserva en el token, pero nunca se registra como identificador reutilizable. |
| 5 | Los números no tienen signo. | `-12` produce `OPERATOR('-')` seguido de `INTEGER('12')`; `+` y `-` nunca forman parte del número. |
| 6 | `INTEGER` es `[0-9]+` y `REAL` es `[0-9]+\.[0-9]+`. | No se aceptan exponentes, `.5`, `5.` ni signos como formas numéricas. |
| 7 | Los átomos simples conservan sus comillas. | Se validan escapes, pero no se eliminan comillas ni se normaliza el lexema. |
| 8 | Las cadenas dobles conservan sus comillas. | Usan los mismos escapes, cambiando `\'` por `\"`. |
| 9 | Un escape desconocido es error léxico. | Nunca se acepta o normaliza silenciosamente. |
| 10 | `%` inicia comentario de línea; `/*` inicia comentario de bloque. | La línea termina antes de `\r` o `\n`; el bloque termina en el primer `*/` y no es anidable. |
| 11 | Las posiciones son 1-based. | Espacio y tabulación avanzan una columna; un salto de línea incrementa la línea y reinicia la columna en 1. `\r\n` cuenta como un único salto de línea. |
| 12 | `is` y `mod` son operadores aritméticos solamente como lexemas completos. | `isla` y `modulo` son átomos completos; `is` y `mod` tienen prioridad de operador en un empate con `ATOM`. |
| 13 | Se admite `-->`. | Se clasifica como operador de familia `DCG`. |
| 14 | `.` aislado es `DOT`. | Si el punto participa en una forma numérica inválida, se informa `MALFORMED_NUMBER` y no se emite `DOT` para ese fragmento. |

## 3. Notación de expresiones regulares

En la forma matemática se usan estas abreviaturas:

```text
LOWER = {a, b, ..., z}
UPPER = {A, B, ..., Z}
LETTER = LOWER ∪ UPPER
DIGIT = {0, 1, ..., 9}
ID_CONT = LETTER ∪ DIGIT ∪ {_}
```

La concatenación se escribe yuxtaponiendo expresiones, `|` representa unión, `*`
cerradura de Kleene y `+` cerradura positiva. Una clase como `[A-Za-z]` representa
exactamente caracteres ASCII, no todas las letras Unicode.

Las expresiones de la columna Python son patrones para `re` de Python escritos como
cadenas crudas (`r"..."`). Deben aplicarse desde la posición actual y con coincidencia
completa del lexema candidato (`match` anclado al cursor o `fullmatch` sobre el
fragmento), no como búsquedas en cualquier parte de la entrada. Python `re` solamente
ejecuta la expresión; no construye por sí solo el autómata integrado del lexer.

Para los literales, `SAFE_SINGLE` y `SAFE_DOUBLE` significan cualquier carácter de
entrada excepto barra inversa, salto de línea y la comilla delimitadora correspondiente.
Esto permite Unicode dentro de las comillas, pero una comilla delimitadora interna debe
estar escapada.

## 4. Catálogo de tokens

En todas las filas, el lexema del token es el segmento original de entrada, sin
normalización. La columna **Tabla de lexemas** indica si además se deduplica una entrada
en la tabla. La clave de deduplicación propuesta es `(tipo_de_token, lexema_original)`;
por tanto, dos apariciones idénticas comparten entrada y dos formas textuales distintas
no se fusionan.

| Token exacto | Descripción exclusivamente léxica | Expresión matemática | Python `re` compatible | Ejemplos válidos | Inválidos o exclusiones | Atributo asociado | Tabla de lexemas |
|---|---|---|---|---|---|---|---|
| `ATOM` | Palabra no entrecomillada iniciada por minúscula ASCII. | `LOWER (LOWER ∪ DIGIT ∪ {_})*` | `r"[a-z][a-z0-9_]*"` | `padre`, `persona_1`, `is_` | `Padre` no es `ATOM`; `a-b` no es un átomo único; `á` no es identificador ASCII. | Ninguno. | **Registrar** lexema original y reutilizar entrada para repeticiones. |
| `QUOTED_ATOM` | Átomo delimitado por comillas simples. Puede contener espacios, caracteres especiales y Unicode conforme al esquema de escapes. | `' (SAFE_SINGLE \| ESC_SINGLE)* '` donde `ESC_SINGLE = \\(\\ \| \' \| n \| r \| t)` | `r"'(?:[^\\'\r\n]|\\[\\'nrt])*'"` | `'Juan Pérez'`, `':-'`, `'it\'s'`, `'ruta\\tmp'`, `'línea\n'` | `'sin cierre`; `'a\q'`; una comilla simple interna sin escape. `\"` no es escape válido aquí. | Ninguno; las comillas forman parte del lexema. | **Registrar** usando el lexema entrecomillado exacto; no des-escapar ni quitar comillas. |
| `VARIABLE` | Variable nombrada por mayúscula ASCII o por `_` seguido de al menos un carácter permitido. | `UPPER ID_CONT* \| _ ID_CONT+` | `r"(?:[A-Z][A-Za-z0-9_]*|_[A-Za-z0-9_]+)"` | `X`, `Persona`, `_Temporal`, `_1`, `A_2` | `_` es `ANONYMOUS_VARIABLE`; `9X` no es variable; `á` y `ñ` no son inicios válidos. | Ninguno; no se resuelve su alcance. | **Registrar** lexema original, sin deducir identidad semántica. |
| `ANONYMOUS_VARIABLE` | El lexema formado por un único guion bajo. | `_` | `r"_"` | `_` | `_X`, `__`, `_1` son `VARIABLE`, no anónimos. | Ninguno. | **Ignorar para la tabla** como identificador reutilizable, aunque el token conserve `_`. |
| `INTEGER` | Secuencia no vacía de dígitos ASCII sin signo ni punto. | `DIGIT+` | `r"[0-9]+"` | `0`, `25`, `0007` | `-25` no es un entero firmado; `5.` y `.5` son errores numéricos; `1e3` no es esta forma numérica. | Ninguno; se conserva la representación textual. | **Registrar** como literal por `(INTEGER, lexema)`, sin convertirlo en esta etapa. |
| `REAL` | Secuencia de dígitos, punto y dígitos, sin signo. | `DIGIT+ \. DIGIT+` | `r"[0-9]+\.[0-9]+"` | `3.14`, `0.5`, `10.00` | `5.`, `.5`, `1.2.3`, `1e-2` no son `REAL`; tampoco `-3.14`. | Ninguno; el punto pertenece al lexema. | **Registrar** como literal por `(REAL, lexema)`, sin convertirlo en esta etapa. |
| `STRING` | Literal delimitado por comillas dobles con contenido y escapes definidos. | `" (SAFE_DOUBLE \| ESC_DOUBLE)* "` donde `ESC_DOUBLE = \\(\\ \| \" \| n \| r \| t)` | `r'''"(?:[^\\"\r\n]|\\[\\"nrt])*"'''` | `"hola"`, `"Juan Pérez"`, `"dice: \"sí\""`, `"ruta\\tmp"`, `"línea\n"` | `"sin cierre`; `"a\q"`; `"a\'b"` (`\'` no es escape de cadena doble); salto de línea real sin escape. | Ninguno; no se interpreta el contenido. | **Registrar** lexema original por `(STRING, lexema)`, sin des-escapar. |
| `OPERATOR` | Uno de los operadores finitos del subconjunto. | Unión de las alternativas de la sección 5. | `OPERATOR_RE` de la sección 5 | `:-`, `?-`, `\==`, `=..`, `//`, `is`, `\+`, `!` | `:` solo, `?` solo, `\` sola y operadores no listados son errores; `isla` no se parte. | `family`: `CLAUSE`, `QUERY`, `DCG`, `UNIFICATION_COMPARISON`, `ARITHMETIC` o `CONTROL`. | **Conservar en el token; no registrar** como lexema identificador. |
| `LPAREN` | Delimitador de apertura de paréntesis. | `(` | `r"\("` | `(` | No se comprueba que exista un `RPAREN` posterior. | Ninguno. | **Conservar en el token; no registrar**. |
| `RPAREN` | Delimitador de cierre de paréntesis. | `)` | `r"\)"` | `)` | No se comprueba que corresponda a una apertura. | Ninguno. | **Conservar en el token; no registrar**. |
| `LBRACKET` | Delimitador de apertura de lista. | `[` | `r"\["` | `[` | No se valida contenido ni cierre. | Ninguno. | **Conservar en el token; no registrar**. |
| `RBRACKET` | Delimitador de cierre de lista. | `]` | `r"\]"` | `]` | No se valida correspondencia con una apertura. | Ninguno. | **Conservar en el token; no registrar**. |
| `LBRACE` | Delimitador de apertura de llaves. | `{` | `r"\{"` | `{` | No se valida contenido ni cierre. | Ninguno. | **Conservar en el token; no registrar**. |
| `RBRACE` | Delimitador de cierre de llaves. | `}` | `r"\}"` | `}` | No se valida correspondencia con una apertura. | Ninguno. | **Conservar en el token; no registrar**. |
| `BAR` | Barra vertical del subconjunto. | `\|` | `r"\|"` | `|` | No se decide si representa tail de lista u otra construcción. | Ninguno. | **Conservar en el token; no registrar**. |
| `COMMA` | Coma separadora. También puede funcionar como conjunción en Prolog, pero esa interpretación no pertenece al lexer. | `,` | `r","` | `,` | No se clasifica como operador distinto ni se valida su posición. | Ninguno. | **Conservar en el token; no registrar**. |
| `DOT` | Punto aislado que no forma parte de un número. | `\.` | `r"\."` | `.` | `5.` y `.5` se diagnostican como número mal formado; no se emite `DOT` para el punto involucrado. | Ninguno. | **Conservar en el token; no registrar**. |

### 4.1 Literales entrecomillados y escapes

Un escape válido está formado por exactamente dos caracteres: barra inversa y uno de
los caracteres permitidos. Por ejemplo, `"\n"` en la fuente contiene una barra
inversa seguida de `n`; no contiene un salto de línea. Los escapes se validan
léxicamente, pero el token conserva ambos caracteres.

| Tipo de literal | Escape válido | Escape desconocido |
|---|---|---|
| `QUOTED_ATOM` | `\\`, `\'`, `\n`, `\r`, `\t` | `\"`, `\q`, `\0` y cualquier otra combinación producen `INVALID_ESCAPE`. |
| `STRING` | `\\`, `\"`, `\n`, `\r`, `\t` | `\'`, `\q`, `\0` y cualquier otra combinación producen `INVALID_ESCAPE`. |

No se permite un salto de línea real dentro de ninguno de los dos literales. Una
comilla delimitadora sin escape termina el literal; la comilla siguiente, si existe,
se procesa desde una nueva posición léxica.

## 5. Operadores y atributos por familia

Cada operador produce el mismo tipo `OPERATOR` y conserva el atributo `family`. El
atributo no expresa precedencia, asociatividad ni aridad.

| Familia (`family`) | Lexemas exactos | Ejemplos válidos |
|---|---|---|
| `CLAUSE` | `:-` | `:-` |
| `QUERY` | `?-` | `?-` |
| `DCG` | `-->` | `-->` |
| `UNIFICATION_COMPARISON` | `=`, `\=`, `==`, `\==`, `=..`, `<`, `=<`, `>`, `>=` | `X = Y`, `X \== Y`, `X =.. L` como fragmentos léxicos |
| `ARITHMETIC` | `+`, `-`, `*`, `/`, `//`, `**`, `is`, `mod` | `X+1`, `X // 2`, `Y is 3`, `N mod 2` |
| `CONTROL` | `\+`, `!`, `;` | `\+ Goal`, `!`, `A ; B` como fragmentos léxicos |

La clasificación de `is` y `mod` aplica cuando el lexema completo es exactamente esa
palabra. El patrón de palabra usa una guarda de continuación `(?![A-Za-z0-9_])` en
Python `re`; así, `isla` coincide como `ATOM` completo, no como `OPERATOR('is')`
seguido de `ATOM('la')`. No se requiere espacio para separar tokens: `is(` permite
`OPERATOR('is')` y `LPAREN` porque `(` no es carácter de continuación.

Para dejar la implementación sin ambigüedad, la unión normativa, separada por
alternativas, es la siguiente:

```text
\\== | \\= | =\.\. | == | =< | >= | :- | \?\- | // | \*\* | \\\+ | --> |
= | < | > | / | \+ | - | \* | ! | ; | is(?![A-Za-z0-9_]) | mod(?![A-Za-z0-9_])
```

La forma Python preferida para copiar en una implementación posterior es:

```python
OPERATOR_RE = (
    r"(?:\\==|\\=|=\.\.|==|=<|>=|:-|\?\-|//|\*\*|\\\+|-->|"
    r"=|<|>|/|\+|-|\*|!|;|"
    r"is(?![A-Za-z0-9_])|mod(?![A-Za-z0-9_]))"
)
```

> **Nota contractual sobre la expresión anterior:** la representación Python usa dos
> caracteres `\\` para reconocer una barra inversa de la entrada. Por ejemplo, la
> alternativa `r"\\=="` reconoce los tres caracteres `\==`, y `r"\\\+"` reconoce
> `\+`. La tabla de operadores y la regla de máxima coincidencia son la autoridad
> semántica si una herramienta visualiza las barras de forma confusa.

## 6. Espacios y comentarios ignorables

Estos elementos no generan tokens ni entradas en la tabla de lexemas, pero sí actualizan
la posición del cursor:

| Elemento | Esquema | Regla |
|---|---|---|
| Espacio y tabulación | `[ \t]+` | Un espacio o tabulación consume una columna. |
| Salto de línea | `\r\n`, `\r` o `\n` | Cada secuencia representa un salto lógico: línea `+1`, columna `=1`. |
| Comentario de línea | `%[^\r\n]*` | Consume `%` y todo hasta antes de `\r` o `\n`; el salto queda para la regla de posición. |
| Comentario de bloque | `/\*(?:[^*]|\*(?!/))*\*/` | Consume desde `/*` hasta el primer `*/`, puede abarcar líneas y no es anidable. |

Ejemplos de la tabla: `% comentario` y `/* comentario */` son comentarios válidos e
ignorables; `/* comentario` es un comentario de bloque sin cierre y produce
`UNTERMINATED_BLOCK_COMMENT`. La secuencia `\v` no pertenece a los espacios definidos
por este contrato y produce `INVALID_CHARACTER`; solamente espacio ASCII, tabulación,
`\r` y `\n` se ignoran.

El patrón Python del comentario de bloque puede escribirse como:

```python
BLOCK_COMMENT_RE = r"/\*(?:[^*]|\*(?!/))*\*/"
LINE_COMMENT_RE = r"%[^\r\n]*"
```

Dentro de un literal entrecomillado, `%`, `/*` y `*/` son contenido del literal y no
inician ni terminan comentarios. Fuera de literales, el reconocimiento de comentarios
debe ocurrir antes de tratar `/` o `*` como operadores.

## 7. Recorrido, máxima coincidencia y prioridades

El contrato de recorrido es:

1. Inicializar el cursor en índice de entrada 0, línea 1 y columna 1.
2. Mientras no se alcance EOF, procesar la posición actual.
3. Consumir espacios, saltos y comentarios sin emitir token; repetir este paso porque
   pueden aparecer varios elementos ignorables consecutivos.
4. En una posición no ignorable, obtener todos los candidatos aplicables que comiencen
   exactamente allí.
5. Elegir el candidato de mayor longitud (**máxima coincidencia**). Si dos candidatos
   tienen igual longitud, usar la prioridad contractual de abajo.
6. Crear el token con el tipo, lexema original, atributo si corresponde y la línea y
   columna de inicio. Actualizar la posición por todos los caracteres consumidos.
7. Si ningún candidato es válido, registrar un error recuperable y consumir lo indicado
   en la sección 8; luego continuar.

Prioridades que deben estar presentes en la especificación de reglas, de izquierda a
derecha cuando hay prefijos comunes:

1. `\==` antes de `\=`.
2. `=..` antes de `=`.
3. `==` antes de `=`.
4. `=<` antes de `<`.
5. `>=` antes de `>`.
6. `:-` antes de diagnosticar `:` como inválido.
7. `?-` antes de diagnosticar `?` como inválido.
8. `//` antes de `/`.
9. `**` antes de `*`.
10. `\+` antes de diagnosticar una barra inversa inválida.
11. `-->` antes de `-`.
12. `REAL` antes de `INTEGER` cuando el prefijo numérico coincide.
13. `_` como `ANONYMOUS_VARIABLE` antes de la regla general de variables.

La máxima coincidencia y las guardas de palabra resuelven además estos casos:

- `isla` gana como `ATOM('isla')` frente al prefijo `OPERATOR('is')`;
- `modulo` gana como `ATOM('modulo')` frente al prefijo `OPERATOR('mod')`;
- `is` y `mod` tienen igual longitud como átomo y operador, por lo que gana
  `OPERATOR` por la regla explícita de palabras reservadas aritméticas;
- `_Tmp` gana como `VARIABLE` completo, mientras `_` aislado gana como
  `ANONYMOUS_VARIABLE`;
- `3.14` gana como `REAL` completo, no como `INTEGER('3')`, `DOT` y `INTEGER('14')`;
- `5.` y `.5` se detectan antes de aplicar `DOT`, porque el punto participa en una
  forma numérica inválida.

No se exige un separador entre tokens distintos. Por ejemplo, `X=Y` produce
`VARIABLE`, `OPERATOR` y `VARIABLE`; la ausencia de espacios no es un error léxico.

### 7.1 Tabla de casos límite

Los resultados son secuencias de tokens; `family=...` muestra el atributo del operador.

| Entrada | Candidatos relevantes | Regla ganadora | Resultado |
|---|---|---|---|
| `\==` | `\==`, `\=` | Máxima coincidencia; `\==` aparece antes | `OPERATOR('\==', family=UNIFICATION_COMPARISON)` |
| `\=` | `\=` | No existe candidato más largo | `OPERATOR('\=', family=UNIFICATION_COMPARISON)` |
| `=..` | `=..`, `=` | Máxima coincidencia | `OPERATOR('=..', family=UNIFICATION_COMPARISON)` |
| `==` | `==`, `=` | Máxima coincidencia | `OPERATOR('==', family=UNIFICATION_COMPARISON)` |
| `=<` | `=<`, `<` | Máxima coincidencia | `OPERATOR('=<', family=UNIFICATION_COMPARISON)` |
| `>=` | `>=`, `>` | Máxima coincidencia | `OPERATOR('>=', family=UNIFICATION_COMPARISON)` |
| `:-` | `:-`, `:` inválido | Operador de dos caracteres | `OPERATOR(':-', family=CLAUSE)` |
| `?-` | `?-`, `?` inválido | Operador de dos caracteres | `OPERATOR('?-', family=QUERY)` |
| `//` | `//`, `/` | Máxima coincidencia | `OPERATOR('//', family=ARITHMETIC)` |
| `**` | `**`, `*` | Máxima coincidencia | `OPERATOR('**', family=ARITHMETIC)` |
| `\+` | `\+`, `\` inválida | Operador de dos caracteres | `OPERATOR('\+', family=CONTROL)` |
| `-->` | `-->`, `-` | Máxima coincidencia | `OPERATOR('-->', family=DCG)` |
| `_` | `_`, `VARIABLE` no aplicable | Regla del anónimo | `ANONYMOUS_VARIABLE('_')` |
| `_Tmp` | `VARIABLE` completo | Máxima coincidencia | `VARIABLE('_Tmp')` |
| `is` | `ATOM`, `OPERATOR` de igual longitud | Prioridad de palabra reservada | `OPERATOR('is', family=ARITHMETIC)` |
| `isla` | `ATOM('isla')`, prefijo `is` | Máxima coincidencia y guarda de palabra | `ATOM('isla')` |
| `modulo` | `ATOM('modulo')`, prefijo `mod` | Máxima coincidencia y guarda de palabra | `ATOM('modulo')` |
| `3.14` | `REAL`, `INTEGER('3')` | Máxima coincidencia; `REAL` antes de `INTEGER` | `REAL('3.14')` |
| `.` | `DOT` | El punto no participa en número | `DOT('.')` |
| `5.` | `INTEGER`, `DOT`, candidato numérico inválido | Detector de número mal formado | Error `MALFORMED_NUMBER('5.')`, sin `DOT` |
| `.5` | `DOT`, `INTEGER`, candidato numérico inválido | Detector de número mal formado | Error `MALFORMED_NUMBER('.5')`, sin `DOT` |
| `1.2.3` | `REAL` parcial, candidato numérico inválido | Se consume la corrida numérica completa | Error `MALFORMED_NUMBER('1.2.3')` |
| `/* x */` | comentario, `/`, `*` | Comentario antes de operadores | Se ignora todo el comentario |
| `/* x` | comentario sin cierre, `/`, `*` | Detector de comentario sin cierre | Error `UNTERMINATED_BLOCK_COMMENT` y consumo hasta EOF |

## 8. Errores léxicos y recuperación

Los errores no son tokens del catálogo. Se acumulan en una colección separada para que
el recorrido pueda continuar. Cada diagnóstico debe incluir como mínimo:

```text
kind, fragment, line, column, message
```

`line` y `column` son la posición de inicio del fragmento problemático. Los nombres de
`kind` de esta tabla son nombres contractuales para la implementación futura, no código
ya existente.

| Error contractual | Ejemplo | Detección | Recuperación obligatoria |
|---|---|---|---|
| `UNTERMINATED_QUOTED_ATOM` | `'Juan` seguido de EOF o salto real | Se abrió `'` y no apareció una comilla simple válida antes de línea/EOF. | Descartar el fragmento hasta antes del salto o hasta EOF; no emitir `QUOTED_ATOM`; continuar en la siguiente posición si existe. |
| `UNTERMINATED_STRING` | `"Juan` seguido de EOF o salto real | Se abrió `"` y no apareció una comilla doble válida antes de línea/EOF. | Descartar el fragmento hasta antes del salto o hasta EOF; no emitir `STRING`. |
| `INVALID_ESCAPE` | `'a\q'`, `"a\'b"` | La barra inversa no está seguida por un escape permitido para ese delimitador. | Registrar el error en la barra inversa, consumir la pareja de escape y seguir buscando el cierre; si el literal cierra, no emitir un token para el literal inválido. |
| `UNTERMINATED_BLOCK_COMMENT` | `/* comentario` | Se abrió `/*` y no apareció `*/` antes de EOF. | Registrar el error y consumir hasta EOF actualizando posiciones; no emitir tokens por el contenido. |
| `MALFORMED_NUMBER` | `5.`, `.5`, `1.2.3` | La corrida numérica de dígitos y puntos no tiene exactamente el formato entero o real. | Consumir la corrida contigua de `[0-9.]`, registrar un error y continuar desde el primer carácter posterior. |
| `INVALID_CHARACTER` | `@`, `:`, `?`, `\`, `á` fuera de comillas | No existe regla válida en la posición actual. | Registrar el carácter y consumir un carácter de entrada; continuar. `:` y `?` solo son válidos como partes de `:-` y `?-`. |

Si un literal contiene varios escapes desconocidos, se registra un `INVALID_ESCAPE` por
cada escape detectado. Si además no cierra, se registra también el error de cierre. No
se inventa un token parcial para una cadena o átomo inválido.

El detector numérico se activa cuando el cursor está en un dígito o en `.` seguido de
un dígito. Consume la máxima corrida contigua de dígitos y puntos. Así, un punto aislado
continúa siendo `DOT`, mientras que el punto de `5.` o `.5` queda incluido en el
fragmento del error.

## 9. Posiciones y formato de token

Cada token emitido debe contener, conceptualmente:

```text
(tipo, lexema_original, línea_inicio, columna_inicio, atributo_opcional)
```

La línea y columna son 1-based y apuntan al primer carácter del lexema, no al carácter
posterior. Los espacios y comentarios no generan huecos artificiales en la entrada:
simplemente actualizan el cursor. Una tabulación avanza exactamente una columna, sin
expandirse a tabuladores de ancho fijo.

Reglas de actualización:

- carácter ordinario: `columna += 1`;
- tabulación: `columna += 1`;
- `\n` o `\r` aislado: `línea += 1`, `columna = 1`;
- `\r\n`: `línea += 1`, `columna = 1` una sola vez.

No se emite `EOF` como token. EOF es solamente la condición que termina el recorrido.

## 10. Tabla de lexemas

La tabla de lexemas es una estructura léxica, no una tabla de símbolos semántica. Se
registran sin duplicados innecesarios:

- `ATOM`, `QUOTED_ATOM` y `VARIABLE`, usando el tipo y el lexema original como clave;
- `INTEGER`, `REAL` y `STRING`, porque son literales conservables del flujo léxico.

`ANONYMOUS_VARIABLE` no se registra: cada `_` representa una aparición anónima
independiente y no un identificador reutilizable. Operadores, delimitadores, espacios y
comentarios tampoco se registran. La tabla no guarda alcance, posiciones de usos,
unificaciones ni tipos semánticos. Si un token necesita una referencia a la entrada,
esa referencia es un índice puramente léxico; el lexema y su posición siguen estando
disponibles en el token.

## 11. Trazabilidad contractual

Los nombres de la columna **Constante futura** son identificadores contractuales para la
implementación siguiente. No implican que exista hoy una clase, enum o módulo con esos
nombres. No se fija un módulo nuevo: la implementación deberá reutilizar la estructura
existente del repositorio.

Los identificadores de prueba son casos previstos, no resultados ejecutados en esta
etapa.

| Token | Expresión regular | Constante futura de implementación | Casos de prueba previstos |
|---|---|---|---|
| `ATOM` | `[a-z][a-z0-9_]*` | `ATOM` | `V-ATOM-01 padre`, `V-ATOM-02 persona_1`, `V-ATOM-03 isla`, `E-ATOM-01 á fuera de comillas` |
| `QUOTED_ATOM` | `'(?:[^\\'\r\n]|\\[\\'nrt])*'` | `QUOTED_ATOM` | `V-QATOM-01 'Juan Pérez'`, `V-QATOM-02 'it\'s'`, `E-QATOM-01 'sin cierre`, `E-QATOM-02 'a\q'` |
| `VARIABLE` | `(?:[A-Z][A-Za-z0-9_]*|_[A-Za-z0-9_]+)` | `VARIABLE` | `V-VAR-01 X`, `V-VAR-02 _Temporal`, `V-VAR-03 _1`, `P-PRIO-01 _/_Tmp` |
| `ANONYMOUS_VARIABLE` | `_` | `ANONYMOUS_VARIABLE` | `V-ANON-01 _`, `P-PRIO-01 _/_Tmp` |
| `INTEGER` | `[0-9]+` | `INTEGER` | `V-INT-01 25`, `V-INT-02 0007`, `P-SIGN-01 -12` |
| `REAL` | `[0-9]+\.[0-9]+` | `REAL` | `V-REAL-01 3.14`, `V-REAL-02 0.5`, `P-REAL-01 3.14/3` |
| `STRING` | `"(?:[^\\"\r\n]|\\[\\"nrt])*"` | `STRING` | `V-STRING-01 "hola"`, `V-STRING-02 "dice: \"sí\""`, `E-STRING-01 "a\q"`, `E-STRING-02 "sin cierre` |
| `OPERATOR` | Unión normativa de la sección 5 | `OPERATOR` con atributo `family` | `V-OP-CLAUSE`, `V-OP-QUERY`, `V-OP-DCG`, `V-OP-COMP`, `V-OP-ARITH`, `V-OP-CONTROL`, `P-OP-01` a `P-OP-09` |
| `LPAREN` | `\(` | `LPAREN` | `V-DELIM-01 (` |
| `RPAREN` | `\)` | `RPAREN` | `V-DELIM-02 )`, `P-SYNTAX-01 )` (sin validar balance) |
| `LBRACKET` | `\[` | `LBRACKET` | `V-DELIM-03 [` |
| `RBRACKET` | `\]` | `RBRACKET` | `V-DELIM-04 ]` |
| `LBRACE` | `\{` | `LBRACE` | `V-DELIM-05 {` |
| `RBRACE` | `\}` | `RBRACE` | `V-DELIM-06 }` |
| `BAR` | `\|` | `BAR` | `V-BAR-01 |` |
| `COMMA` | `,` | `COMMA` | `V-COMMA-01 ,`, `P-COMMA-01` como conjunción solo léxica |
| `DOT` | `\.` | `DOT` | `V-DOT-01 .`, `P-DOT-01 5.`, `P-DOT-02 .5` |

Las reglas ignorables se trazan aparte porque no son tokens:

| Elemento | Expresión | Constante/acción futura | Casos previstos |
|---|---|---|---|
| Espacios | `[ \t\r\n]+` con tratamiento de `\r\n` | `SKIP_WHITESPACE` | `V-POS-01` |
| Comentario de línea | `%[^\r\n]*` | `SKIP_LINE_COMMENT` | `V-COMMENT-01 % comentario\nX` |
| Comentario de bloque | `/\*(?:[^*]|\*(?!/))*\*/` | `SKIP_BLOCK_COMMENT` | `V-COMMENT-02`, `E-COMMENT-01 /* sin cierre` |

## 12. Criterios de no ambigüedad para la implementación posterior

1. Las coincidencias se intentan en la posición actual; no se salta un carácter válido
   para buscar una coincidencia posterior.
2. Se usa máxima coincidencia y, solo en empate, prioridad explícita.
3. Los operadores de varios caracteres preceden a sus prefijos de un carácter según la
   lista de la sección 7.
4. `is` y `mod` se comprueban como alternativas completas y ganan el empate con
   `ATOM`; no se reservan sus prefijos dentro de palabras más largas.
5. Un número mal formado se diagnostica como una unidad numérica cuando comienza por
   dígito o por punto seguido de dígito; no se fragmenta artificialmente en números y
   puntos válidos.
6. Los literales conservan texto, comillas y escapes. Un error de escape no se corrige
   reemplazando la secuencia por su valor interpretado.
7. Los comentarios y espacios se descartan solamente de la salida, nunca del conteo de
   posiciones.
8. Todos los delimitadores se reconocen por separado. La corrección de su balance o
   contexto pertenece a una fase posterior.

## 13. Fuentes consultadas

Se revisaron antes de redactar esta especificación:

Las rutas siguientes están escritas relativas a la raíz del repositorio (`Tarea01TC`):

1. `Tarea INFO1148 sem2_2026.pdf`, enunciado de la tarea de análisis léxico.
2. `agents.md`, instrucciones y alcance inicial del repositorio.
3. `../teoria-computacion/clases/semana2/sesion1_TC.pdf`, contenidos sobre compiladores,
   análisis léxico, tabla de símbolos, manejo de errores, alfabetos y palabras.
4. `../teoria-computacion/clases/semana3/sesion4_Lenguajes_Regulares.html`, contenidos
   sobre expresiones regulares, autómatas finitos y límites de los lenguajes regulares.
5. `../teoria-computacion/tareas/Formato Informe Tarea.pdf`, estructura sugerida del
   informe, especificación léxica, prioridades, tabla de lexemas, errores y pruebas.

Las tres fuentes de `teoria-computacion` se encuentran como directorio hermano del
repositorio, tal como confirma `agents.md`; no se copiaron ni modificaron.
