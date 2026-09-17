"""Errores léxicos recuperables del subconjunto Prolog.

Contrato: docs/informe/01_especificacion_lexica.md, sección 8.
Los errores no son tokens; se acumulan en una colección separada.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorKind(str, Enum):
    """Nombres contractuales de error (sección 8)."""

    UNTERMINATED_QUOTED_ATOM = "UNTERMINATED_QUOTED_ATOM"
    UNTERMINATED_STRING = "UNTERMINATED_STRING"
    INVALID_ESCAPE = "INVALID_ESCAPE"
    UNTERMINATED_BLOCK_COMMENT = "UNTERMINATED_BLOCK_COMMENT"
    MALFORMED_NUMBER = "MALFORMED_NUMBER"
    INVALID_CHARACTER = "INVALID_CHARACTER"


@dataclass(frozen=True)
class LexError:
    """Diagnóstico mínimo: kind, fragment, line, column, message."""

    kind: ErrorKind
    fragment: str
    line: int
    column: int
    message: str
