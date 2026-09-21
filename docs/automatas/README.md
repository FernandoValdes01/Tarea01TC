# Autómatas del analizador léxico

Esta carpeta formaliza los reconocedores del subconjunto de Prolog definido en
[`../informe/01_especificacion_lexica.md`](../informe/01_especificacion_lexica.md).
No amplía el catálogo de tokens ni cambia sus expresiones regulares.

## Contenido

- [`01_automatas_principales.md`](01_automatas_principales.md): AFD de átomos,
  variables y números; autómatas de literales, comentarios y operadores.
- [`02_determinacion_y_minimizacion.md`](02_determinacion_y_minimizacion.md):
  estrategia integrada equivalente, construcción de subconjuntos para
  `{=, ==, \=, \==}` y minimización completa.
- [`diagramas/`](diagramas/): fuentes Mermaid editables (`.mmd`) y figuras
  renderizadas (`.svg`). Los documentos explican también cada figura mediante
  definiciones y tablas, por lo que su lectura no depende del renderizador.

## Convenciones

Se usa la notación de clases del contrato léxico:

```text
LOWER   = {a, ..., z}
UPPER   = {A, ..., Z}
LETTER  = LOWER ∪ UPPER
DIGIT   = {0, ..., 9}
ID_CONT = LETTER ∪ DIGIT ∪ {_}
```

Un AFN se escribe como `(Q, Σ, s, F, Δ)` y un AFD como
`(Q, Σ, δ, s, F)`. En los diagramas, `inicio` es una pseudoflecha, los estados
cuya etiqueta incluye `/ TOKEN` son aceptores y `∅` es el estado muerto. Una
transición que no aparece va a `∅`; cuando se muestra `∅`, este tiene bucle para
todo `Σ`.

La yuxtaposición expresa concatenación en una expresión regular. El carácter
literal punto se escribe `.` dentro de un lexema y `\.` en una expresión regular.
Por tanto, el punto de `3.14` es un símbolo de entrada, no un operador de
concatenación.

## Regeneración de figuras

Los archivos `.mmd` son las fuentes editables. Los SVG incluidos se generaron
con Mermaid CLI 11.17.0 y fondo blanco. Pueden regenerarse con cualquier versión
compatible con `stateDiagram-v2`:

```bash
mmdc -i docs/automatas/diagramas/atomos.mmd \
  -o docs/automatas/diagramas/atomos.svg \
  -t default -b white
```

Mermaid CLI se usa como herramienta externa. El repositorio no la incorpora
como dependencia. Si se ejecuta mediante `npx` y Puppeteer solicita el
navegador, instálelo una vez con:

```bash
npx --yes puppeteer browsers install chrome-headless-shell
```

## Inclusión en el informe PDF

Los diagramas editables Mermaid se renderizan y componen en páginas A4 mediante:

```bash
python tools/build_report_diagrams.py
```

El resultado es `docs/informe/automatas_appendix.pdf`. El informe completo se
genera desde el Markdown canónico y agrega automáticamente este anexo con:

```bash
python tools/build_final_report.py
```

El entregable resultante es `docs/informe/Tarea_Fernando_Valdes.pdf`.
