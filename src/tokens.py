"""Tipos y representación de tokens del subconjunto Prolog.

Contrato: docs/informe/01_especificacion_lexica.md, secciones 4 y 5.
El lexema conservado es siempre el segmento original de entrada, sin normalización.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    """Nombres contractuales de token (sección 4)."""

    ATOM = "ATOM"
    QUOTED_ATOM = "QUOTED_ATOM"
    VARIABLE = "VARIABLE"
    ANONYMOUS_VARIABLE = "ANONYMOUS_VARIABLE"
    INTEGER = "INTEGER"
    REAL = "REAL"
    STRING = "STRING"
    OPERATOR = "OPERATOR"
    LPAREN = "LPAREN"
    RPAREN = "RPAREN"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    BAR = "BAR"
    COMMA = "COMMA"
    DOT = "DOT"


class OperatorFamily(str, Enum):
    """Atributo `family` de OPERATOR (sección 5)."""

    CLAUSE = "CLAUSE"
    QUERY = "QUERY"
    DCG = "DCG"
    UNIFICATION_COMPARISON = "UNIFICATION_COMPARISON"
    ARITHMETIC = "ARITHMETIC"
    CONTROL = "CONTROL"


#: Familia por lexema exacto de operador (sección 5).
OPERATOR_FAMILY: dict[str, OperatorFamily] = {
    ":-": OperatorFamily.CLAUSE,
    "?-": OperatorFamily.QUERY,
    "-->": OperatorFamily.DCG,
    "=": OperatorFamily.UNIFICATION_COMPARISON,
    "\\=": OperatorFamily.UNIFICATION_COMPARISON,
    "==": OperatorFamily.UNIFICATION_COMPARISON,
    "\\==": OperatorFamily.UNIFICATION_COMPARISON,
    "=..": OperatorFamily.UNIFICATION_COMPARISON,
    "<": OperatorFamily.UNIFICATION_COMPARISON,
    "=<": OperatorFamily.UNIFICATION_COMPARISON,
    ">": OperatorFamily.UNIFICATION_COMPARISON,
    ">=": OperatorFamily.UNIFICATION_COMPARISON,
    "+": OperatorFamily.ARITHMETIC,
    "-": OperatorFamily.ARITHMETIC,
    "*": OperatorFamily.ARITHMETIC,
    "/": OperatorFamily.ARITHMETIC,
    "//": OperatorFamily.ARITHMETIC,
    "**": OperatorFamily.ARITHMETIC,
    "is": OperatorFamily.ARITHMETIC,
    "mod": OperatorFamily.ARITHMETIC,
    "\\+": OperatorFamily.CONTROL,
    "!": OperatorFamily.CONTROL,
    ";": OperatorFamily.CONTROL,
}


@dataclass(frozen=True)
class Token:
    """Un token con tipo, lexema original y posición 1-based de inicio.

    `family` solo se usa con OPERATOR. `table_index` es un índice puramente
    léxico a la tabla de lexemas cuando el tipo es registrable, o None.
    """

    type: TokenType
    lexeme: str
    line: int
    column: int
    family: OperatorFamily | None = None
    table_index: int | None = None
