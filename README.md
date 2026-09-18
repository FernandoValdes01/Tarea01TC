# Análisis léxico de Prolog

Proyecto de la tarea de Teoría de la Computación, curso INFO1148.

Analizador léxico de un subconjunto de Prolog con recorrido de izquierda a derecha, máxima coincidencia y prioridades explícitas. Emite tipo, lexema original, línea y columna por token, administra una tabla de lexemas y reporta errores recuperables con ubicación y fragmento.

## Requisitos

Solo se usa la biblioteca estándar de Python 3.10 o posterior. La suite de pruebas requiere `pytest` como dependencia de desarrollo.

## Instalación

```bash
pip install -r requirements.txt
```

En este entorno la suite también se ejecutó sin instalación global mediante `uv run --with pytest python -m pytest -q`.

## Ejecución del lexer

```bash
python -m src.main tests/corpus/entradas/programa_valido.pl
python -m src.main tests/corpus/entradas/programa_con_errores.pl
python -m src.main archivo.pl --tabla
python -m src.main archivo.pl --show-attributes
```

La salida normal lista un token por línea como `<TIPO, 'lexema', línea, columna>`. `--show-attributes` agrega la familia o el índice léxico y `--tabla` vuelca la tabla de lexemas. Los errores se imprimen en `stderr`; el código de salida es 1 si hubo errores y 0 si no.

## Ejecución de pruebas

```bash
python -m compileall src tests
python -m pytest -q
git diff --check
```

Resultado real de la integración: 85 pruebas aprobadas y cero fallos.

## Estructura

- `src/`: código del analizador léxico (`tokens.py`, `errors.py`, `symbol_table.py`, `lexer.py`, `main.py`).
- `tests/`: pruebas (`test_lexer.py`) y corpus (`corpus/validos/`, `corpus/invalidos/`, `corpus/entradas/` con `programa_valido.pl` y `programa_con_errores.pl`).
- `docs/`: informe, autómatas y referencias (`docs/informe/01_especificacion_lexica.md`, `docs/informe/04_matriz_de_pruebas.md`, `docs/informe/informe_tecnico.md`, `docs/informe/referencias.md`, `docs/informe/anexos.md`, PDF final y fuente LaTeX).

## Formato de salida

Cada token contiene tipo, lexema original sin normalización, línea y columna 1-based de inicio y, solo para `OPERATOR`, el atributo `family` (`CLAUSE`, `QUERY`, `DCG`, `UNIFICATION_COMPARISON`, `ARITHMETIC`, `CONTROL`).

## Política de errores

Los errores no son tokens y se acumulan para continuar el análisis: átomo o string sin cierre, comentario de bloque sin cierre (consume hasta EOF), carácter no admitido, número mal formado y escape desconocido. Cada diagnóstico incluye clase, fragmento, línea, columna y mensaje.

## Alcance y exclusiones

Se reconoce exactamente el subconjunto del contrato en `docs/informe/01_especificacion_lexica.md`. No se realiza análisis sintáctico ni semántico: no se valida el orden de los tokens, el balance de delimitadores, los ámbitos, la unificación ni la validez de un programa.
