"""Diagnósticos estructurados producidos por el lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LexicalErrorKind(str, Enum):
    """Tipos de error fijados por el contrato léxico."""

    UNTERMINATED_QUOTED_ATOM = "UNTERMINATED_QUOTED_ATOM"
    UNTERMINATED_STRING = "UNTERMINATED_STRING"
    INVALID_ESCAPE = "INVALID_ESCAPE"
    UNTERMINATED_BLOCK_COMMENT = "UNTERMINATED_BLOCK_COMMENT"
    MALFORMED_NUMBER = "MALFORMED_NUMBER"
    INVALID_CHARACTER = "INVALID_CHARACTER"


@dataclass(frozen=True, slots=True)
class LexicalError:
    """Error recuperable con ubicación y fragmento de entrada."""

    message: str
    line: int
    column: int
    fragment: str
    kind: LexicalErrorKind = LexicalErrorKind.INVALID_CHARACTER

    def __str__(self) -> str:
        return (
            f"[{self.kind.value}] línea {self.line}, columna {self.column}: "
            f"{self.message}; fragmento {self.fragment!r}"
        )
