"""Analizador léxico para el subconjunto contractual de Prolog."""

from __future__ import annotations

import re

from .errors import LexicalError, LexicalErrorKind
from .symbol_table import STORED_TOKEN_TYPES, SymbolTable
from .tokens import Token, TokenType


ASCII_LOWER = frozenset("abcdefghijklmnopqrstuvwxyz")
ASCII_UPPER = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
ASCII_DIGITS = frozenset("0123456789")
ID_CONT = ASCII_LOWER | ASCII_UPPER | ASCII_DIGITS | {"_"}
ATOM_CONT = ASCII_LOWER | ASCII_DIGITS | {"_"}
INTEGER_RE = re.compile(r"[0-9]+")
REAL_RE = re.compile(r"[0-9]+\.[0-9]+")

OPERATOR_FAMILIES: dict[str, str] = {
    ":-": "CLAUSE",
    "?-": "QUERY",
    "-->": "DCG",
    "=": "UNIFICATION_COMPARISON",
    r"\=": "UNIFICATION_COMPARISON",
    "==": "UNIFICATION_COMPARISON",
    r"\==": "UNIFICATION_COMPARISON",
    "=..": "UNIFICATION_COMPARISON",
    "<": "UNIFICATION_COMPARISON",
    "=<": "UNIFICATION_COMPARISON",
    ">": "UNIFICATION_COMPARISON",
    ">=": "UNIFICATION_COMPARISON",
    "+": "ARITHMETIC",
    "-": "ARITHMETIC",
    "*": "ARITHMETIC",
    "/": "ARITHMETIC",
    "//": "ARITHMETIC",
    "**": "ARITHMETIC",
    "is": "ARITHMETIC",
    "mod": "ARITHMETIC",
    r"\+": "CONTROL",
    "!": "CONTROL",
    ";": "CONTROL",
}

SYMBOLIC_OPERATORS = tuple(
    sorted(
        (operator for operator in OPERATOR_FAMILIES if operator not in {"is", "mod"}),
        key=len,
        reverse=True,
    )
)

DELIMITERS: dict[str, TokenType] = {
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
    "[": TokenType.LBRACKET,
    "]": TokenType.RBRACKET,
    "{": TokenType.LBRACE,
    "}": TokenType.RBRACE,
    "|": TokenType.BAR,
    ",": TokenType.COMMA,
    ".": TokenType.DOT,
}


class Lexer:
    """Recorre texto de izquierda a derecha y acumula tokens y errores."""

    def __init__(self, source_text: str, *, symbol_table: SymbolTable | None = None) -> None:
        if not isinstance(source_text, str):
            raise TypeError("source_text debe ser str")
        self.source = source_text
        self.symbol_table = symbol_table if symbol_table is not None else SymbolTable()
        self.tokens: list[Token] = []
        self.errors: list[LexicalError] = []
        self.index = 0
        self.line = 1
        self.column = 1

    def tokenize(self) -> list[Token]:
        """Tokeniza la entrada completa y devuelve los tokens emitidos."""

        self.tokens = []
        self.errors = []
        self.index = 0
        self.line = 1
        self.column = 1

        while not self._at_end:
            char = self._current

            if char in " \t\r\n":
                self._skip_whitespace()
            elif char == "%":
                self._skip_line_comment()
            elif self.source.startswith("/*", self.index):
                self._skip_block_comment()
            elif char in {"'", '"'}:
                self._scan_literal(char)
            elif char in ASCII_DIGITS or (
                char == "." and self._peek() in ASCII_DIGITS
            ):
                self._scan_number()
            elif char in ASCII_LOWER or char in ASCII_UPPER or char == "_":
                self._scan_identifier()
            elif not self._scan_operator() and not self._scan_delimiter():
                self._invalid_character()

        return self.tokens

    @property
    def _at_end(self) -> bool:
        return self.index >= len(self.source)

    @property
    def _current(self) -> str:
        return "" if self._at_end else self.source[self.index]

    def _peek(self, offset: int = 1) -> str:
        position = self.index + offset
        return "" if position >= len(self.source) else self.source[position]

    def _advance_text(self, text: str) -> None:
        """Avanza por texto bruto y actualiza una sola vez cada salto lógico."""

        offset = 0
        while offset < len(text):
            char = text[offset]
            if char == "\r":
                if offset + 1 < len(text) and text[offset + 1] == "\n":
                    offset += 2
                else:
                    offset += 1
                self.line += 1
                self.column = 1
            elif char == "\n":
                offset += 1
                self.line += 1
                self.column = 1
            else:
                offset += 1
                self.column += 1
        self.index += len(text)

    def _consume_to(self, end: int) -> str:
        fragment = self.source[self.index:end]
        self._advance_text(fragment)
        return fragment

    def _skip_whitespace(self) -> None:
        end = self.index + 1
        while end < len(self.source) and self.source[end] in " \t\r\n":
            end += 1
        self._consume_to(end)

    def _skip_line_comment(self) -> None:
        end = self.index + 1
        while end < len(self.source) and self.source[end] not in "\r\n":
            end += 1
        self._consume_to(end)

    def _skip_block_comment(self) -> None:
        start_line, start_column = self.line, self.column
        closing = self.source.find("*/", self.index + 2)
        if closing >= 0:
            self._consume_to(closing + 2)
            return

        fragment = self.source[self.index :]
        self._add_error(
            LexicalErrorKind.UNTERMINATED_BLOCK_COMMENT,
            "comentario de bloque sin cierre",
            fragment,
            start_line,
            start_column,
        )
        self._advance_text(fragment)

    def _scan_literal(self, delimiter: str) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        token_type = TokenType.QUOTED_ATOM if delimiter == "'" else TokenType.STRING
        unterminated_kind = (
            LexicalErrorKind.UNTERMINATED_QUOTED_ATOM
            if delimiter == "'"
            else LexicalErrorKind.UNTERMINATED_STRING
        )
        valid_escapes = {"\\", delimiter, "n", "r", "t"}
        position = start + 1
        invalid = False

        while position < len(self.source):
            char = self.source[position]
            if char in "\r\n":
                fragment = self.source[start:position]
                self._add_error(
                    unterminated_kind,
                    "literal sin delimitador de cierre",
                    fragment,
                    start_line,
                    start_column,
                )
                self._consume_to(position)
                return
            if char == delimiter:
                fragment = self.source[start : position + 1]
                if not invalid:
                    self._emit(token_type, fragment, start_line, start_column)
                else:
                    self._advance_text(fragment)
                return
            if char == "\\":
                escaped = self.source[position + 1] if position + 1 < len(self.source) else ""
                if escaped not in valid_escapes:
                    escape_fragment = self.source[position : min(position + 2, len(self.source))]
                    self._add_error(
                        LexicalErrorKind.INVALID_ESCAPE,
                        "secuencia de escape no admitida",
                        escape_fragment,
                        start_line,
                        start_column + (position - start),
                    )
                    invalid = True
                # Un salto físico no queda oculto por una barra inversa: en la
                # siguiente iteración se aplica la recuperación por fin de línea.
                position += 1 if escaped in "\r\n" else (2 if escaped else 1)
                continue
            position += 1

        fragment = self.source[start:position]
        self._add_error(
            unterminated_kind,
            "literal sin delimitador de cierre",
            fragment,
            start_line,
            start_column,
        )
        self._advance_text(fragment)

    def _scan_number(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        end = start

        # Primero se consume la corrida numérica tradicional. Si aparece un
        # sufijo de identificador (por ejemplo, ``12abc``), también pertenece al
        # fragmento inválido; un punto posterior a ese sufijo vuelve a ser un
        # separador seguro y se procesa en la siguiente iteración.
        while end < len(self.source) and (
            self.source[end] in ASCII_DIGITS or self.source[end] == "."
        ):
            end += 1
        if end < len(self.source) and self.source[end] in ID_CONT:
            while end < len(self.source) and self.source[end] in ID_CONT:
                end += 1
        fragment = self.source[start:end]

        if REAL_RE.fullmatch(fragment):
            self._emit(TokenType.REAL, fragment, start_line, start_column)
        elif INTEGER_RE.fullmatch(fragment):
            self._emit(TokenType.INTEGER, fragment, start_line, start_column)
        else:
            self._add_error(
                LexicalErrorKind.MALFORMED_NUMBER,
                "número fuera de los formatos INTEGER y REAL",
                fragment,
                start_line,
                start_column,
            )
            self._advance_text(fragment)

    def _scan_identifier(self) -> None:
        start = self.index
        start_line, start_column = self.line, self.column
        first = self._current
        end = start + 1

        if first in ASCII_LOWER:
            while end < len(self.source) and self.source[end] in ATOM_CONT:
                end += 1
            lexeme = self.source[start:end]
            following = self.source[end] if end < len(self.source) else ""
            if lexeme in {"is", "mod"} and following not in ID_CONT:
                self._emit(
                    TokenType.OPERATOR,
                    lexeme,
                    start_line,
                    start_column,
                    OPERATOR_FAMILIES[lexeme],
                )
            else:
                self._emit(TokenType.ATOM, lexeme, start_line, start_column)
            return

        while end < len(self.source) and self.source[end] in ID_CONT:
            end += 1
        lexeme = self.source[start:end]
        token_type = (
            TokenType.ANONYMOUS_VARIABLE
            if first == "_" and len(lexeme) == 1
            else TokenType.VARIABLE
        )
        self._emit(token_type, lexeme, start_line, start_column)

    def _scan_operator(self) -> bool:
        for operator in SYMBOLIC_OPERATORS:
            if self.source.startswith(operator, self.index):
                self._emit(
                    TokenType.OPERATOR,
                    operator,
                    self.line,
                    self.column,
                    OPERATOR_FAMILIES[operator],
                )
                return True
        return False

    def _scan_delimiter(self) -> bool:
        token_type = DELIMITERS.get(self._current)
        if token_type is None:
            return False
        self._emit(token_type, self._current, self.line, self.column)
        return True

    def _invalid_character(self) -> None:
        fragment = self._current
        self._add_error(
            LexicalErrorKind.INVALID_CHARACTER,
            "carácter sin regla léxica",
            fragment,
            self.line,
            self.column,
        )
        self._advance_text(fragment)

    def _emit(
        self,
        token_type: TokenType,
        lexeme: str,
        line: int,
        column: int,
        attribute: object | None = None,
    ) -> None:
        if token_type in STORED_TOKEN_TYPES:
            attribute = self.symbol_table.register(token_type, lexeme)
        self.tokens.append(Token(token_type, lexeme, line, column, attribute))
        self._advance_text(lexeme)

    def _add_error(
        self,
        kind: LexicalErrorKind,
        message: str,
        fragment: str,
        line: int,
        column: int,
    ) -> None:
        self.errors.append(
            LexicalError(
                message=message,
                line=line,
                column=column,
                fragment=fragment,
                kind=kind,
            )
        )
