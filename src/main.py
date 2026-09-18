"""Interfaz de terminal del analizador léxico."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .lexer import Lexer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analiza léxicamente un archivo del subconjunto de Prolog."
    )
    parser.add_argument("input_file", type=Path, help="archivo de entrada UTF-8")
    parser.add_argument(
        "--show-attributes",
        action="store_true",
        help="muestra familia de operador o índice de tabla junto al token",
    )
    parser.add_argument(
        "--tabla",
        action="store_true",
        help="muestra la tabla de lexemas al final",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        source = args.input_file.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        print(f"No se pudo leer {args.input_file}: {error}", file=sys.stderr)
        return 2

    lexer = Lexer(source)
    tokens = lexer.tokenize()

    for token in tokens:
        print(token.format(include_attribute=args.show_attributes))

    if args.tabla:
        print("--- tabla de lexemas ---")
        for entry in lexer.symbol_table:
            print(
                f"{entry.index}: "
                f"<{entry.token_type.value}, {entry.original_lexeme!r}>"
            )

    if lexer.errors:
        print("Errores léxicos:", file=sys.stderr)
        for error in lexer.errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
