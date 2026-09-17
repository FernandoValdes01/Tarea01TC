# Análisis léxico de Prolog

Proyecto de la tarea de Teoría de la Computación, curso INFO1148.

## Estructura

- `src/`: código del analizador léxico.
- `tests/`: pruebas y corpus de entradas.
- `docs/`: informe, autómatas y referencias.

## Uso

El proyecto requiere Python 3.10 o posterior y no tiene dependencias externas. Para
analizar un archivo UTF-8:

```bash
python -m src.main ruta/al/archivo.pl
```

El programa imprime los tokens en `stdout`. Los errores recuperables se muestran en
`stderr` y producen el código de salida `1`, sin ocultar los tokens reconocidos. Para
incluir el índice de la tabla de lexemas o la familia de cada operador:

```bash
python -m src.main --show-attributes ruta/al/archivo.pl
```

Las pruebas se ejecutan con:

```bash
python -m unittest discover -v
```
