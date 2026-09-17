"""Punto de entrada del analizador léxico de Prolog."""

from __future__ import annotations

import argparse
import sys

from .lexer import tokenize_file


def build_parser() -> argparse.ArgumentParser:
    """Crea el parser de argumentos de la CLI."""
    parser = argparse.ArgumentParser(
        description="Analizador léxico de un subconjunto de Prolog."
    )
    parser.add_argument("archivo", help="ruta al archivo fuente .pl")
    parser.add_argument(
        "--tabla",
        action="store_true",
        help="muestra la tabla de lexemas al final",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Ejecuta la CLI y retorna el código de salida."""
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = tokenize_file(args.archivo)
    except FileNotFoundError:
        print(f"error: no se encontró el archivo {args.archivo!r}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: no se pudo leer el archivo: {exc}", file=sys.stderr)
        return 1

    for token in result.tokens:
        extra = f" {token.family.value}" if token.family is not None else ""
        print(f"<{token.type.value}, {token.lexeme!r}, {token.line}, {token.column}>{extra}")
    for error in result.errors:
        print(
            f"ERROR {error.kind.value} {error.fragment!r} "
            f"{error.line}:{error.column} {error.message}"
        )
    if args.tabla:
        print("--- tabla de lexemas ---")
        for idx, (token_type, lexeme) in enumerate(result.symbol_table.entries()):
            print(f"{idx}: <{token_type.value}, {lexeme!r}>")
    return 1 if result.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
