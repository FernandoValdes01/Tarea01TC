"""Tipos y representación pública de los tokens del lexer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TokenType(str, Enum):
    """Categorías léxicas del subconjunto de Prolog."""

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
    """Familias contractuales de operadores."""

    CLAUSE = "CLAUSE"
    QUERY = "QUERY"
    DCG = "DCG"
    UNIFICATION_COMPARISON = "UNIFICATION_COMPARISON"
    ARITHMETIC = "ARITHMETIC"
    CONTROL = "CONTROL"


OPERATOR_FAMILY: dict[str, OperatorFamily] = {
    ":-": OperatorFamily.CLAUSE,
    "?-": OperatorFamily.QUERY,
    "-->": OperatorFamily.DCG,
    "=": OperatorFamily.UNIFICATION_COMPARISON,
    r"\=": OperatorFamily.UNIFICATION_COMPARISON,
    "==": OperatorFamily.UNIFICATION_COMPARISON,
    r"\==": OperatorFamily.UNIFICATION_COMPARISON,
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
    r"\+": OperatorFamily.CONTROL,
    "!": OperatorFamily.CONTROL,
    ";": OperatorFamily.CONTROL,
}


@dataclass(frozen=True, slots=True)
class Token:
    """Token emitido, con lexema original y posición inicial 1-based."""

    type: TokenType
    lexeme: str
    line: int
    column: int
    attribute: object | None = None
    family: OperatorFamily | None = None
    table_index: int | None = None

    def __post_init__(self) -> None:
        """Sincroniza la API contractual con los campos del corpus integrado."""

        family = self.family
        table_index = self.table_index
        attribute = self.attribute

        if self.type is TokenType.OPERATOR:
            if family is None and isinstance(attribute, (str, OperatorFamily)):
                try:
                    family = OperatorFamily(attribute)
                except ValueError:
                    family = None
            if attribute is None and family is not None:
                attribute = family
        elif table_index is None and isinstance(attribute, int):
            table_index = attribute
        elif attribute is None and table_index is not None:
            attribute = table_index

        object.__setattr__(self, "attribute", attribute)
        object.__setattr__(self, "family", family)
        object.__setattr__(self, "table_index", table_index)

    def format(self, *, include_attribute: bool = False) -> str:
        """Devuelve la forma del enunciado y, opcionalmente, el atributo."""

        fields = [self.type.name, repr(self.lexeme), str(self.line), str(self.column)]
        if include_attribute and self.attribute is not None:
            value = (
                self.attribute.value
                if isinstance(self.attribute, OperatorFamily)
                else self.attribute
            )
            fields.append(repr(value))
        return f"<{', '.join(fields)}>"

    def __str__(self) -> str:
        return self.format()
