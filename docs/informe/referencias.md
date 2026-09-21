# Referencias

Solo se listan fuentes efectivamente consultadas, en formato APA 7. No se inventaron editoriales, autores, URL ni fechas. Las decisiones propias del grupo viven en `docs/informe/01_especificacion_lexica.md` y se mantienen separadas de las fuentes académicas.

- Lévano, M. (2026). _Tarea: análisis léxico del lenguaje Prolog. Investigación, análisis, diseño, implementación y validación_ (INFO1148, sem2_2026). Enunciado del curso. [Documento PDF del repositorio: `Tarea INFO1148 sem2_2026.pdf`.]
- Especificación léxica contractual del subconjunto de Prolog. (2026). [`docs/informe/01_especificacion_lexica.md`.] (Decisión propia del grupo: catálogo de tokens, expresiones regulares, prioridades, tabla de lexemas y errores.)
- Matriz de pruebas del lexer de Prolog. (2026). [`docs/informe/04_matriz_de_pruebas.md`.] (Evidencia propia: 26 casos válidos, 22 de prioridad, 16 inválidos y resultado real de 85 aprobadas.)
- Código fuente del analizador léxico. (2026). Repositorio Tarea01TC [`src/tokens.py`, `src/errors.py`, `src/symbol_table.py`, `src/lexer.py`, `src/main.py`] y corpus de pruebas [`tests/test_lexer.py`, `tests/corpus/`]. https://github.com/FernandoValdes01/Tarea01TC
- Python Software Foundation. (2026). _Regular expression operations (re)_. Documentación oficial de Python 3. https://docs.python.org/3/library/re.html (Consultada para la semántica de `re.match` anclado al cursor, las guardas negativas y `fullmatch` en la validación numérica.)
- pytest-dev team. (2026). _pytest documentation_. https://docs.pytest.org/ (Consultada para la parametrización con identificadores y la ejecución con `python -m pytest -q`; en este entorno se ejecutó mediante `uv run --with pytest`.)
- Astral Software. (2026). _uv documentation_. https://docs.astral.sh/uv/ (Consultada para ejecutar la suite sin instalación global con `uv run --with pytest`.)
- ISO/IEC. (1995). _ISO/IEC 13211-1:1995. Information technology — Programming languages — Prolog — Part 1: General core_. Citada como referencia general de la notación que inspira el subconjunto; el alcance exigible es el del enunciado y el del contrato, no la norma completa.

## Fuentes locales de organización

- Las instrucciones de trabajo usadas durante la preparación fueron proporcionadas externamente y no forman parte del repositorio entregable.
- `../teoria-computacion/tareas/Formato Informe Tarea.pdf` fue consultado para la portada, la organización del informe, las tablas de especificación, errores y pruebas, y la presentación de anexos. Sus orientaciones se aplicaron sin conservar placeholders.
