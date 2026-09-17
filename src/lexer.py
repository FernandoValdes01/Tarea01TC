"""Analizador léxico del subconjunto Prolog.

Contrato: docs/informe/01_especificacion_lexica.md, secciones 6 a 9.
Recorrido de izquierda a derecha con máxima coincidencia y prioridades
explícitas. Sin análisis sintáctico ni semántico.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .errors import ErrorKind, LexError
from .symbol_table import SymbolTable
from .tokens import OPERATOR_FAMILY, OperatorFamily, Token, TokenType

ATOM_RE = re.compile(r"[a-z][a-z0-9_]*")
VARIABLE_RE = re.compile(r"(?:[A-Z][A-Za-z0-9_]*|_[A-Za-z0-9_]+)")
INTEGER_RE = re.compile(r"[0-9]+")
REAL_RE = re.compile(r"[0-9]+\.[0-9]+")
NUM_RUN_RE = re.compile(r"[0-9.]+")

# Unión normativa de la sección 5. El orden deja los prefijos largos primero
# para que `match` desde el cursor respete máxima coincidencia.
OPERATOR_RE = re.compile(
    r"(?:\\==|\\=|=\.\.|==|=<|>=|:-|\?-|//|\*\*|\\\+|-->|"
    r"=|<|>|/|\+|-|\*|!|;|"
    r"is(?![A-Za-z0-9_])|mod(?![A-Za-z0-9_]))"
)

_SINGLE_DELIMS: dict[str, TokenType] = {
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

_REGISTRABLE = frozenset(
    {
        TokenType.ATOM,
        TokenType.QUOTED_ATOM,
        TokenType.VARIABLE,
        TokenType.INTEGER,
        TokenType.REAL,
        TokenType.STRING,
    }
)

_SINGLE_QUOTE_ESCAPES = frozenset({"\\", "'", "n", "r", "t"})
_DOUBLE_QUOTE_ESCAPES = frozenset({"\\", '"', "n", "r", "t"})

_ID_CONT = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_"
)


@dataclass
class LexResult:
    """Salida del lexer: tokens en orden, errores acumulados y tabla."""

    tokens: list[Token] = field(default_factory=list)
    errors: list[LexError] = field(default_factory=list)
    symbol_table: SymbolTable = field(default_factory=SymbolTable)


def _is_id_cont(ch: str) -> bool:
    return ch in _ID_CONT


def tokenize(source: str) -> LexResult:
    """Tokeniza `source` según el contrato y retorna tokens, errores y tabla."""
    result = LexResult()
    tokens = result.tokens
    errors = result.errors
    table = result.symbol_table

    n = len(source)
    i = 0
    line = 1
    col = 1

    def advance_one() -> None:
        nonlocal i, line, col
        if i >= n:
            return
        ch = source[i]
        if ch == "\r" and i + 1 < n and source[i + 1] == "\n":
            i += 2
            line += 1
            col = 1
        elif ch == "\r" or ch == "\n":
            i += 1
            line += 1
            col = 1
        else:
            i += 1
            col += 1

    def advance_to(target: int) -> None:
        while i < target:
            advance_one()

    def emit(
        token_type: TokenType,
        lexeme: str,
        start_line: int,
        start_col: int,
        family: OperatorFamily | None = None,
    ) -> None:
        table_index: int | None = None
        if token_type in _REGISTRABLE:
            table_index = table.intern(token_type, lexeme)
        tokens.append(
            Token(
                type=token_type,
                lexeme=lexeme,
                line=start_line,
                column=start_col,
                family=family,
                table_index=table_index,
            )
        )

    def scan_literal(
        start: int, start_line: int, start_col: int, quote: str
    ) -> None:
        """Escanea un literal entrecomillado desde `start` (la comilla)."""
        nonlocal i, line, col
        if quote == "'":
            allowed = _SINGLE_QUOTE_ESCAPES
            unterminated_kind = ErrorKind.UNTERMINATED_QUOTED_ATOM
            token_type = TokenType.QUOTED_ATOM
            label = "átomo entre comillas simples"
        else:
            allowed = _DOUBLE_QUOTE_ESCAPES
            unterminated_kind = ErrorKind.UNTERMINATED_STRING
            token_type = TokenType.STRING
            label = "string con comillas dobles"

        j = start + 1
        pending_escapes: list[LexError] = []
        while j < n:
            ch = source[j]
            if ch == "\r" or ch == "\n":
                fragment = source[start:j]
                for err in pending_escapes:
                    errors.append(err)
                errors.append(
                    LexError(
                        kind=unterminated_kind,
                        fragment=fragment,
                        line=start_line,
                        column=start_col,
                        message=f"{label} sin cierre antes del salto de línea",
                    )
                )
                advance_to(j)
                return
            if ch == "\\":
                if j + 1 >= n:
                    fragment = source[start : j + 1]
                    for err in pending_escapes:
                        errors.append(err)
                    errors.append(
                        LexError(
                            kind=unterminated_kind,
                            fragment=fragment,
                            line=start_line,
                            column=start_col,
                            message=f"{label} sin cierre al fin de la entrada",
                        )
                    )
                    advance_to(n)
                    return
                nxt = source[j + 1]
                if nxt == "\r" or nxt == "\n":
                    fragment = source[start:j]
                    for err in pending_escapes:
                        errors.append(err)
                    errors.append(
                        LexError(
                            kind=unterminated_kind,
                            fragment=fragment,
                            line=start_line,
                            column=start_col,
                            message=f"{label} sin cierre antes del salto de línea",
                        )
                    )
                    advance_to(j)
                    return
                if nxt not in allowed:
                    # Columna de la barra inversa (sin saltos dentro del literal).
                    esc_col = start_col + (j - start)
                    pending_escapes.append(
                        LexError(
                            kind=ErrorKind.INVALID_ESCAPE,
                            fragment=source[j : j + 2],
                            line=start_line,
                            column=esc_col,
                            message=(
                                f"escape desconocido {source[j : j + 2]!r} "
                                f"en {label}"
                            ),
                        )
                    )
                j += 2
                continue
            if ch == quote:
                fragment = source[start : j + 1]
                if pending_escapes:
                    for err in pending_escapes:
                        errors.append(err)
                    # Literal inválido: no se emite token (sección 8).
                else:
                    emit(token_type, fragment, start_line, start_col)
                advance_to(j + 1)
                return
            j += 1
        # EOF sin cierre.
        fragment = source[start:n]
        for err in pending_escapes:
            errors.append(err)
        errors.append(
            LexError(
                kind=unterminated_kind,
                fragment=fragment,
                line=start_line,
                column=start_col,
                message=f"{label} sin cierre al fin de la entrada",
            )
        )
        advance_to(n)

    while True:
        # 3. Consumir ignorables (pueden aparecer consecutivos).
        skipped = True
        while skipped and i < n:
            skipped = False
            ch = source[i]
            if ch == " " or ch == "\t":
                advance_one()
                skipped = True
            elif ch == "\r" or ch == "\n":
                advance_one()
                skipped = True
            elif ch == "%":
                j = i + 1
                while j < n and source[j] != "\r" and source[j] != "\n":
                    j += 1
                advance_to(j)
                skipped = True
            elif ch == "/" and i + 1 < n and source[i + 1] == "*":
                start = i
                start_line = line
                start_col = col
                end = source.find("*/", i + 2)
                if end == -1:
                    fragment = source[start:n]
                    errors.append(
                        LexError(
                            kind=ErrorKind.UNTERMINATED_BLOCK_COMMENT,
                            fragment=fragment,
                            line=start_line,
                            column=start_col,
                            message="comentario de bloque sin cierre */",
                        )
                    )
                    advance_to(n)
                else:
                    advance_to(end + 2)
                skipped = True
        if i >= n:
            break

        start = i
        start_line = line
        start_col = col
        ch = source[i]

        # 5/12. Números y detector de número mal formado: dígito o `.`+dígito.
        if ch.isascii() and ch.isdigit():
            match = NUM_RUN_RE.match(source, i)
            assert match is not None
            fragment = match.group(0)
            if REAL_RE.fullmatch(fragment):
                emit(TokenType.REAL, fragment, start_line, start_col)
            elif INTEGER_RE.fullmatch(fragment):
                emit(TokenType.INTEGER, fragment, start_line, start_col)
            else:
                errors.append(
                    LexError(
                        kind=ErrorKind.MALFORMED_NUMBER,
                        fragment=fragment,
                        line=start_line,
                        column=start_col,
                        message=(
                            f"número mal formado {fragment!r}: "
                            "se esperaba entero o real con dígitos a ambos "
                            "lados del punto"
                        ),
                    )
                )
            advance_to(i + len(fragment))
            continue
        if ch == "." and i + 1 < n and source[i + 1].isascii() and source[i + 1].isdigit():
            match = NUM_RUN_RE.match(source, i)
            assert match is not None
            fragment = match.group(0)
            if REAL_RE.fullmatch(fragment):
                emit(TokenType.REAL, fragment, start_line, start_col)
            elif INTEGER_RE.fullmatch(fragment):
                emit(TokenType.INTEGER, fragment, start_line, start_col)
            else:
                errors.append(
                    LexError(
                        kind=ErrorKind.MALFORMED_NUMBER,
                        fragment=fragment,
                        line=start_line,
                        column=start_col,
                        message=(
                            f"número mal formado {fragment!r}: "
                            "se esperaba entero o real con dígitos a ambos "
                            "lados del punto"
                        ),
                    )
                )
            advance_to(i + len(fragment))
            continue

        # Literales entrecomillados.
        if ch == "'" or ch == '"':
            scan_literal(start, start_line, start_col, ch)
            continue

        # Operadores (máxima coincidencia por orden de alternativas + guardas).
        op_match = OPERATOR_RE.match(source, i)
        if op_match:
            lexeme = op_match.group(0)
            family = OPERATOR_FAMILY.get(lexeme)
            # `is`/`mod` siempre están en el mapa; los simbólicos también.
            # Si por algún motivo faltara, se informa como carácter inválido.
            if family is not None:
                emit(TokenType.OPERATOR, lexeme, start_line, start_col, family)
                advance_to(i + len(lexeme))
                continue

        # Variables, anónima y átomos (el empate is/mod vs ATOM ya lo ganó
        # OPERATOR porque se comprueba antes con guarda de palabra).
        if ch == "_":
            nxt = source[i + 1] if i + 1 < n else ""
            if nxt != "" and _is_id_cont(nxt):
                var_match = VARIABLE_RE.match(source, i)
                assert var_match is not None
                lexeme = var_match.group(0)
                emit(TokenType.VARIABLE, lexeme, start_line, start_col)
                advance_to(i + len(lexeme))
            else:
                emit(TokenType.ANONYMOUS_VARIABLE, "_", start_line, start_col)
                advance_one()
            continue
        if ch.isascii() and ch.isupper():
            var_match = VARIABLE_RE.match(source, i)
            assert var_match is not None
            lexeme = var_match.group(0)
            emit(TokenType.VARIABLE, lexeme, start_line, start_col)
            advance_to(i + len(lexeme))
            continue
        if ch.isascii() and ch.islower():
            atom_match = ATOM_RE.match(source, i)
            assert atom_match is not None
            lexeme = atom_match.group(0)
            emit(TokenType.ATOM, lexeme, start_line, start_col)
            advance_to(i + len(lexeme))
            continue

        # Delimitadores de un carácter.
        delim = _SINGLE_DELIMS.get(ch)
        if delim is not None:
            emit(delim, ch, start_line, start_col)
            advance_one()
            continue

        # 7. Carácter no admitido (incluye `:`, `?`, `\` aisladas y Unicode
        # fuera de literales). Se consume un carácter y se continúa.
        errors.append(
            LexError(
                kind=ErrorKind.INVALID_CHARACTER,
                fragment=ch,
                line=start_line,
                column=start_col,
                message=f"carácter no admitido {ch!r} fuera de literal",
            )
        )
        advance_one()

    return result


def tokenize_file(path: str, encoding: str = "utf-8") -> LexResult:
    """Lee un archivo Prolog y lo tokeniza."""
    with open(path, encoding=encoding) as handle:
        return tokenize(handle.read())
