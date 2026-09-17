"""Tipos y representación pública de los tokens del lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """Categorías léxicas del subconjunto de Prolog."""

    ATOM = auto()
    QUOTED_ATOM = auto()
    VARIABLE = auto()
    ANONYMOUS_VARIABLE = auto()
    INTEGER = auto()
    REAL = auto()
    STRING = auto()
    OPERATOR = auto()
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    BAR = auto()
    COMMA = auto()
    DOT = auto()


@dataclass(frozen=True, slots=True)
class Token:
    """Token emitido, con lexema original y posición inicial 1-based."""

    type: TokenType
    lexeme: str
    line: int
    column: int
    attribute: object | None = None

    def format(self, *, include_attribute: bool = False) -> str:
        """Devuelve la forma del enunciado y, opcionalmente, el atributo."""

        fields = [self.type.name, repr(self.lexeme), str(self.line), str(self.column)]
        if include_attribute and self.attribute is not None:
            fields.append(repr(self.attribute))
        return f"<{', '.join(fields)}>"

    def __str__(self) -> str:
        return self.format()
