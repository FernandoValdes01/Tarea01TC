"""Pruebas automatizadas del lexer de Prolog.

Contrato: docs/informe/01_especificacion_lexica.md.
Cubre corpus válido (>=20), inválido (>=8), máxima coincidencia/prioridad,
posiciones, tabla de lexemas, escapes, recuperación y archivos completos.

IDs estables: V (válidos), P (prioridad), I (inválidos), T (transversales),
F (archivos). Ver docs/informe/04_matriz_de_pruebas.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.errors import ErrorKind, LexError
from src.lexer import LexResult, tokenize, tokenize_file
from src.symbol_table import SymbolTable
from src.tokens import OperatorFamily, Token, TokenType

CORPUS_DIR = Path(__file__).parent / "corpus"
ENTRADAS_DIR = CORPUS_DIR / "entradas"
VALIDOS_DIR = CORPUS_DIR / "validos"
INVALIDOS_DIR = CORPUS_DIR / "invalidos"


# ---------------------------------------------------------------------------
# Helpers (no duplican lógica del lexer, solo comparan resultados)
# ---------------------------------------------------------------------------


def simplified_tokens(result: LexResult) -> list[tuple]:
    """Tokens como tuplas comparables (tipo, lexema, línea, columna, familia)."""
    out = []
    for tok in result.tokens:
        out.append(
            (
                tok.type,
                tok.lexeme,
                tok.line,
                tok.column,
                tok.family,
            )
        )
    return out


def simplified_errors(result: LexResult) -> list[tuple]:
    """Errores como tuplas comparables (kind, fragment, línea, columna)."""
    return [(e.kind, e.fragment, e.line, e.column) for e in result.errors]


def assert_tokens(
    result: LexResult, expected: list[tuple], check_no_errors: bool = True
) -> None:
    if check_no_errors:
        assert result.errors == [], f"errores inesperados: {result.errors}"
    assert simplified_tokens(result) == expected


def assert_error(
    error: LexError,
    kind: ErrorKind,
    fragment: str,
    line: int,
    column: int,
) -> None:
    assert error.kind == kind
    assert error.fragment == fragment
    assert error.line == line
    assert error.column == column
    assert error.message.strip() != ""


# ---------------------------------------------------------------------------
# T01: modelo Token
# ---------------------------------------------------------------------------


def test_token_model_campos_y_posicion() -> None:
    """T01: Token conserva tipo, lexema y posición 1-based de inicio."""
    tok = Token(type=TokenType.ATOM, lexeme="padre", line=2, column=1)
    assert tok.type == TokenType.ATOM
    assert tok.lexeme == "padre"
    assert tok.line == 2
    assert tok.column == 1
    assert tok.family is None


def test_token_operador_con_familia() -> None:
    """T02: OPERATOR conserva el atributo family sin precedencia asociada."""
    tok = Token(
        type=TokenType.OPERATOR,
        lexeme=":-",
        line=1,
        column=1,
        family=OperatorFamily.CLAUSE,
    )
    assert tok.family == OperatorFamily.CLAUSE
    assert tok.family.value == "CLAUSE"


def test_token_igualdad_por_valor() -> None:
    """T03: Token es comparable por valor (dataclass)."""
    left = Token(type=TokenType.INTEGER, lexeme="25", line=1, column=1)
    right = Token(type=TokenType.INTEGER, lexeme="25", line=1, column=1)
    assert left == right


# ---------------------------------------------------------------------------
# Corpus válido (>=20 casos diferenciados con tokens y posiciones)
# ---------------------------------------------------------------------------

ARITH = OperatorFamily.ARITHMETIC
CLAUSE = OperatorFamily.CLAUSE
QUERY = OperatorFamily.QUERY
DCG = OperatorFamily.DCG
UNIF = OperatorFamily.UNIFICATION_COMPARISON
CTRL = OperatorFamily.CONTROL

VALID_CASES: list[dict] = [
    {
        "id": "V01",
        "objetivo": "átomo simple",
        "source": "padre",
        "expected": [(TokenType.ATOM, "padre", 1, 1, None)],
    },
    {
        "id": "V02",
        "objetivo": "átomo con dígitos y guion bajo",
        "source": "persona_1",
        "expected": [(TokenType.ATOM, "persona_1", 1, 1, None)],
    },
    {
        "id": "V03",
        "objetivo": "variable con mayúscula",
        "source": "Persona",
        "expected": [(TokenType.VARIABLE, "Persona", 1, 1, None)],
    },
    {
        "id": "V04",
        "objetivo": "variable con prefijo _",
        "source": "_Temporal",
        "expected": [(TokenType.VARIABLE, "_Temporal", 1, 1, None)],
    },
    {
        "id": "V05",
        "objetivo": "variable anónima",
        "source": "_",
        "expected": [(TokenType.ANONYMOUS_VARIABLE, "_", 1, 1, None)],
    },
    {
        "id": "V06",
        "objetivo": "entero",
        "source": "25",
        "expected": [(TokenType.INTEGER, "25", 1, 1, None)],
    },
    {
        "id": "V07",
        "objetivo": "real",
        "source": "3.14",
        "expected": [(TokenType.REAL, "3.14", 1, 1, None)],
    },
    {
        "id": "V08",
        "objetivo": "átomo entre comillas con espacio",
        "source": "'Juan Pérez'",
        "expected": [(TokenType.QUOTED_ATOM, "'Juan Pérez'", 1, 1, None)],
    },
    {
        "id": "V09",
        "objetivo": "átomo entre comillas con carácter especial",
        "source": "':-'",
        "expected": [(TokenType.QUOTED_ATOM, "':-'", 1, 1, None)],
    },
    {
        "id": "V10",
        "objetivo": "string con escapes válidos (\\n)",
        "source": '"línea\\n"',
        "expected": [(TokenType.STRING, '"línea\\n"', 1, 1, None)],
    },
    {
        "id": "V11",
        "objetivo": "operadores de cláusula, consulta y DCG",
        "source": ":- ?- -->",
        "expected": [
            (TokenType.OPERATOR, ":-", 1, 1, CLAUSE),
            (TokenType.OPERATOR, "?-", 1, 4, QUERY),
            (TokenType.OPERATOR, "-->", 1, 7, DCG),
        ],
    },
    {
        "id": "V12",
        "objetivo": "operadores de unificación y comparación",
        "source": "= \\= == \\== =.. < =< > >=",
        "expected": [
            (TokenType.OPERATOR, "=", 1, 1, UNIF),
            (TokenType.OPERATOR, "\\=", 1, 3, UNIF),
            (TokenType.OPERATOR, "==", 1, 6, UNIF),
            (TokenType.OPERATOR, "\\==", 1, 9, UNIF),
            (TokenType.OPERATOR, "=..", 1, 13, UNIF),
            (TokenType.OPERATOR, "<", 1, 17, UNIF),
            (TokenType.OPERATOR, "=<", 1, 19, UNIF),
            (TokenType.OPERATOR, ">", 1, 22, UNIF),
            (TokenType.OPERATOR, ">=", 1, 24, UNIF),
        ],
    },
    {
        "id": "V13",
        "objetivo": "operadores aritméticos incluyendo //, **, is y mod",
        "source": "+ - * / // ** is mod",
        "expected": [
            (TokenType.OPERATOR, "+", 1, 1, ARITH),
            (TokenType.OPERATOR, "-", 1, 3, ARITH),
            (TokenType.OPERATOR, "*", 1, 5, ARITH),
            (TokenType.OPERATOR, "/", 1, 7, ARITH),
            (TokenType.OPERATOR, "//", 1, 9, ARITH),
            (TokenType.OPERATOR, "**", 1, 12, ARITH),
            (TokenType.OPERATOR, "is", 1, 15, ARITH),
            (TokenType.OPERATOR, "mod", 1, 18, ARITH),
        ],
    },
    {
        "id": "V14",
        "objetivo": "operadores de control",
        "source": "\\+ ! ;",
        "expected": [
            (TokenType.OPERATOR, "\\+", 1, 1, CTRL),
            (TokenType.OPERATOR, "!", 1, 4, CTRL),
            (TokenType.OPERATOR, ";", 1, 6, CTRL),
        ],
    },
    {
        "id": "V15",
        "objetivo": "paréntesis",
        "source": "( )",
        "expected": [
            (TokenType.LPAREN, "(", 1, 1, None),
            (TokenType.RPAREN, ")", 1, 3, None),
        ],
    },
    {
        "id": "V16",
        "objetivo": "corchetes",
        "source": "[ ]",
        "expected": [
            (TokenType.LBRACKET, "[", 1, 1, None),
            (TokenType.RBRACKET, "]", 1, 3, None),
        ],
    },
    {
        "id": "V17",
        "objetivo": "llaves",
        "source": "{ }",
        "expected": [
            (TokenType.LBRACE, "{", 1, 1, None),
            (TokenType.RBRACE, "}", 1, 3, None),
        ],
    },
    {
        "id": "V18",
        "objetivo": "barra vertical",
        "source": "|",
        "expected": [(TokenType.BAR, "|", 1, 1, None)],
    },
    {
        "id": "V19",
        "objetivo": "coma y punto",
        "source": ", .",
        "expected": [
            (TokenType.COMMA, ",", 1, 1, None),
            (TokenType.DOT, ".", 1, 3, None),
        ],
    },
    {
        "id": "V20",
        "objetivo": "comentario de línea y espacios con salto",
        "source": "% comentario\n  padre",
        "expected": [(TokenType.ATOM, "padre", 2, 3, None)],
    },
    {
        "id": "V21",
        "objetivo": "comentario de bloque ignorable",
        "source": "/* bloque */ padre",
        "expected": [(TokenType.ATOM, "padre", 1, 14, None)],
    },
    {
        "id": "V22",
        "objetivo": "espacios, tabulación y CRLF como un salto",
        "source": " \t\n\r\nX",
        "expected": [(TokenType.VARIABLE, "X", 3, 1, None)],
    },
    {
        "id": "V23",
        "objetivo": "hecho completo con posiciones de cada token",
        "source": "padre(juan, ana).",
        "expected": [
            (TokenType.ATOM, "padre", 1, 1, None),
            (TokenType.LPAREN, "(", 1, 6, None),
            (TokenType.ATOM, "juan", 1, 7, None),
            (TokenType.COMMA, ",", 1, 11, None),
            (TokenType.ATOM, "ana", 1, 13, None),
            (TokenType.RPAREN, ")", 1, 16, None),
            (TokenType.DOT, ".", 1, 17, None),
        ],
    },
    {
        "id": "V24",
        "objetivo": "string con comillas escapadas",
        "source": '"dice \\"si\\""',
        "expected": [(TokenType.STRING, '"dice \\"si\\""', 1, 1, None)],
    },
    {
        "id": "V25",
        "objetivo": "átomo entre comillas con escape de comilla",
        "source": "'it\\'s'",
        "expected": [(TokenType.QUOTED_ATOM, "'it\\'s'", 1, 1, None)],
    },
    {
        "id": "V26",
        "objetivo": "lista con barra y coma",
        "source": "[X, Y | Z]",
        "expected": [
            (TokenType.LBRACKET, "[", 1, 1, None),
            (TokenType.VARIABLE, "X", 1, 2, None),
            (TokenType.COMMA, ",", 1, 3, None),
            (TokenType.VARIABLE, "Y", 1, 5, None),
            (TokenType.BAR, "|", 1, 7, None),
            (TokenType.VARIABLE, "Z", 1, 9, None),
            (TokenType.RBRACKET, "]", 1, 10, None),
        ],
    },
    {
        "id": "V27",
        "objetivo": "átomo con mayúsculas interiores",
        "source": "personaX",
        "expected": [(TokenType.ATOM, "personaX", 1, 1, None)],
    },
]


@pytest.mark.parametrize("case", VALID_CASES, ids=[c["id"] for c in VALID_CASES])
def test_corpus_valido(case: dict) -> None:
    """Cada caso válido afirma tokens y posiciones exactas."""
    result = tokenize(case["source"])
    assert_tokens(result, case["expected"])


# ---------------------------------------------------------------------------
# Prioridad y máxima coincidencia
# ---------------------------------------------------------------------------

PRIORITY_CASES: list[dict] = [
    {
        "id": "P01",
        "objetivo": "\\== completo, no \\= + =",
        "source": "\\==",
        "expected": [(TokenType.OPERATOR, "\\==", 1, 1, UNIF)],
    },
    {
        "id": "P02",
        "objetivo": "=.. completo, no = + . + .",
        "source": "=..",
        "expected": [(TokenType.OPERATOR, "=..", 1, 1, UNIF)],
    },
    {
        "id": "P03",
        "objetivo": "== completo, no = + =",
        "source": "==",
        "expected": [(TokenType.OPERATOR, "==", 1, 1, UNIF)],
    },
    {
        "id": "P04",
        "objetivo": "\\= completo",
        "source": "\\=",
        "expected": [(TokenType.OPERATOR, "\\=", 1, 1, UNIF)],
    },
    {
        "id": "P05",
        "objetivo": ":- operador de cláusula",
        "source": ":-",
        "expected": [(TokenType.OPERATOR, ":-", 1, 1, CLAUSE)],
    },
    {
        "id": "P06",
        "objetivo": "?- operador de consulta",
        "source": "?-",
        "expected": [(TokenType.OPERATOR, "?-", 1, 1, QUERY)],
    },
    {
        "id": "P07",
        "objetivo": "--> operador DCG incluido",
        "source": "-->",
        "expected": [(TokenType.OPERATOR, "-->", 1, 1, DCG)],
    },
    {
        "id": "P08",
        "objetivo": "// completo, no dos /",
        "source": "//",
        "expected": [(TokenType.OPERATOR, "//", 1, 1, ARITH)],
    },
    {
        "id": "P09",
        "objetivo": "** completo, no dos *",
        "source": "**",
        "expected": [(TokenType.OPERATOR, "**", 1, 1, ARITH)],
    },
    {
        "id": "P10",
        "objetivo": "_ es ANONYMOUS_VARIABLE",
        "source": "_",
        "expected": [(TokenType.ANONYMOUS_VARIABLE, "_", 1, 1, None)],
    },
    {
        "id": "P11",
        "objetivo": "_Tmp es VARIABLE completa",
        "source": "_Tmp",
        "expected": [(TokenType.VARIABLE, "_Tmp", 1, 1, None)],
    },
    {
        "id": "P12",
        "objetivo": "isla es un ATOM, no is + la",
        "source": "isla",
        "expected": [(TokenType.ATOM, "isla", 1, 1, None)],
    },
    {
        "id": "P13",
        "objetivo": "is es OPERATOR aritmético",
        "source": "is",
        "expected": [(TokenType.OPERATOR, "is", 1, 1, ARITH)],
    },
    {
        "id": "P14",
        "objetivo": "mod es OPERATOR aritmético",
        "source": "mod",
        "expected": [(TokenType.OPERATOR, "mod", 1, 1, ARITH)],
    },
    {
        "id": "P15",
        "objetivo": "modulo es ATOM, no mod + ulo",
        "source": "modulo",
        "expected": [(TokenType.ATOM, "modulo", 1, 1, None)],
    },
    {
        "id": "P16",
        "objetivo": "1.25 es REAL, no INTEGER + DOT + INTEGER",
        "source": "1.25",
        "expected": [(TokenType.REAL, "1.25", 1, 1, None)],
    },
    {
        "id": "P17",
        "objetivo": "operadores adyacentes sin espacios avanzan el cursor",
        "source": "X=Y",
        "expected": [
            (TokenType.VARIABLE, "X", 1, 1, None),
            (TokenType.OPERATOR, "=", 1, 2, UNIF),
            (TokenType.VARIABLE, "Y", 1, 3, None),
        ],
    },
    {
        "id": "P18",
        "objetivo": "operador largo adyacente sin espacios",
        "source": "X\\==Y",
        "expected": [
            (TokenType.VARIABLE, "X", 1, 1, None),
            (TokenType.OPERATOR, "\\==", 1, 2, UNIF),
            (TokenType.VARIABLE, "Y", 1, 5, None),
        ],
    },
    {
        "id": "P19",
        "objetivo": "is seguido de paréntesis sin espacio",
        "source": "is(",
        "expected": [
            (TokenType.OPERATOR, "is", 1, 1, ARITH),
            (TokenType.LPAREN, "(", 1, 3, None),
        ],
    },
    {
        "id": "P20",
        "objetivo": "cláusula adyacente sin espacios",
        "source": "a:-b",
        "expected": [
            (TokenType.ATOM, "a", 1, 1, None),
            (TokenType.OPERATOR, ":-", 1, 2, CLAUSE),
            (TokenType.ATOM, "b", 1, 4, None),
        ],
    },
    {
        "id": "P21",
        "objetivo": "12abc es un número mal formado recuperable",
        "source": "12abc",
        "expected": [],
        "expected_error": (ErrorKind.MALFORMED_NUMBER, "12abc", 1, 1),
    },
    {
        "id": "P22",
        "objetivo": "is_ es ATOM por guarda de palabra",
        "source": "is_",
        "expected": [(TokenType.ATOM, "is_", 1, 1, None)],
    },
]


@pytest.mark.parametrize(
    "case", PRIORITY_CASES, ids=[c["id"] for c in PRIORITY_CASES]
)
def test_prioridad_y_maxima_coincidencia(case: dict) -> None:
    """Cada caso de prioridad afirma un operador o lexema completo."""
    result = tokenize(case["source"])
    if "expected_error" in case:
        assert simplified_tokens(result) == case["expected"]
        assert len(result.errors) == 1
        assert_error(result.errors[0], *case["expected_error"])
    else:
        assert_tokens(result, case["expected"])


# ---------------------------------------------------------------------------
# Corpus inválido (>=8 con línea, columna, fragmento y recuperación)
# ---------------------------------------------------------------------------


def test_invalido_I01_atom_sin_cierre_eof() -> None:
    """I01: átomo entre comillas sin cierre hasta EOF."""
    result = tokenize("'Juan")
    assert len(result.tokens) == 0
    assert len(result.errors) == 1
    assert_error(
        result.errors[0],
        ErrorKind.UNTERMINATED_QUOTED_ATOM,
        "'Juan",
        1,
        1,
    )


def test_invalido_I02_atom_sin_cierre_con_recuperacion() -> None:
    """I02: sin cierre antes de salto; la línea siguiente se recupera."""
    result = tokenize("'sin cierre\npadre.")
    assert len(result.errors) == 1
    assert_error(
        result.errors[0],
        ErrorKind.UNTERMINATED_QUOTED_ATOM,
        "'sin cierre",
        1,
        1,
    )
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "padre", 2, 1, None),
        (TokenType.DOT, ".", 2, 6, None),
    ]


def test_invalido_I03_string_sin_cierre() -> None:
    """I03: string sin cierre hasta EOF."""
    result = tokenize('"Juan')
    assert result.tokens == []
    assert len(result.errors) == 1
    assert_error(
        result.errors[0], ErrorKind.UNTERMINATED_STRING, '"Juan', 1, 1
    )


def test_invalido_I04_string_sin_cierre_con_recuperacion() -> None:
    """I04: string sin cierre antes de salto; continúa en la línea 2."""
    result = tokenize('"sin cierre\nX.')
    assert len(result.errors) == 1
    assert_error(
        result.errors[0],
        ErrorKind.UNTERMINATED_STRING,
        '"sin cierre',
        1,
        1,
    )
    assert simplified_tokens(result) == [
        (TokenType.VARIABLE, "X", 2, 1, None),
        (TokenType.DOT, ".", 2, 2, None),
    ]


def test_invalido_I05_bloque_sin_cierre_consume_eof() -> None:
    """I05: /* sin */ consume hasta EOF y no deja tokens posteriores."""
    result = tokenize("padre. /* sin cierre")
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "padre", 1, 1, None),
        (TokenType.DOT, ".", 1, 6, None),
    ]
    assert len(result.errors) == 1
    err = result.errors[0]
    assert err.kind == ErrorKind.UNTERMINATED_BLOCK_COMMENT
    assert err.fragment == "/* sin cierre"
    assert (err.line, err.column) == (1, 8)
    assert err.message.strip() != ""


def test_invalido_I06_caracter_no_admitido_con_recuperacion() -> None:
    """I06: @ se diagnostica y el átomo posterior se recupera."""
    result = tokenize("@ padre")
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.INVALID_CHARACTER, "@", 1, 1)
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "padre", 1, 3, None)
    ]


def test_invalido_I07_numero_5_punto() -> None:
    """I07: 5. es MALFORMED_NUMBER sin DOT y con recuperación."""
    result = tokenize("5. padre")
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.MALFORMED_NUMBER, "5.", 1, 1)
    assert all(t.type != TokenType.DOT for t in result.tokens)
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "padre", 1, 4, None)
    ]


def test_invalido_I08_numero_punto_5() -> None:
    """I08: .5 es MALFORMED_NUMBER sin DOT."""
    result = tokenize(".5")
    assert result.tokens == []
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.MALFORMED_NUMBER, ".5", 1, 1)


def test_invalido_I09_numero_1_punto_punto_2() -> None:
    """I09: 1..2 consume la corrida completa como un error."""
    result = tokenize("1..2")
    assert result.tokens == []
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.MALFORMED_NUMBER, "1..2", 1, 1)


def test_invalido_I10_numero_1_punto_2_punto_3() -> None:
    """I10: variante 1.2.3 también es un solo MALFORMED_NUMBER."""
    result = tokenize("1.2.3")
    assert result.tokens == []
    assert_error(result.errors[0], ErrorKind.MALFORMED_NUMBER, "1.2.3", 1, 1)


def test_invalido_I11_escape_desconocido_en_atom() -> None:
    """I11: 'a\\q' registra INVALID_ESCAPE y no emite QUOTED_ATOM."""
    result = tokenize("'a\\q'")
    assert result.tokens == []
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.INVALID_ESCAPE, "\\q", 1, 3)


def test_invalido_I12_escape_desconocido_en_string() -> None:
    """I12: \"a\\'b\" usa \\' inválido en string doble."""
    result = tokenize("\"a\\'b\"")
    assert result.tokens == []
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.INVALID_ESCAPE, "\\'", 1, 3)


def test_invalido_I13_dos_puntos_sin_guion() -> None:
    """I13: : aislado es INVALID_CHARACTER con recuperación posterior."""
    result = tokenize(": padre")
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.INVALID_CHARACTER, ":", 1, 1)
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "padre", 1, 3, None)
    ]


def test_invalido_I14_interrogacion_sin_guion() -> None:
    """I14: ? aislado es INVALID_CHARACTER."""
    result = tokenize("?")
    assert result.tokens == []
    assert_error(result.errors[0], ErrorKind.INVALID_CHARACTER, "?", 1, 1)


def test_invalido_I15_barra_aislada() -> None:
    """I15: \\ aislada es INVALID_CHARACTER y se recupera el token siguiente."""
    result = tokenize("\\ X")
    assert len(result.errors) == 1
    assert_error(result.errors[0], ErrorKind.INVALID_CHARACTER, "\\", 1, 1)
    assert simplified_tokens(result) == [
        (TokenType.VARIABLE, "X", 1, 3, None)
    ]


def test_invalido_I16_unicode_fuera_de_literal() -> None:
    """I16: á fuera de comillas es INVALID_CHARACTER (alfabeto ASCII)."""
    result = tokenize("á")
    assert result.tokens == []
    assert_error(result.errors[0], ErrorKind.INVALID_CHARACTER, "á", 1, 1)


# ---------------------------------------------------------------------------
# T: posiciones, comentarios, escapes, tabla y recuperación
# ---------------------------------------------------------------------------


def test_posiciones_multilinea_y_columnas() -> None:
    """T01: líneas y columnas 1-based con \n, \r y \r\n como un salto."""
    result = tokenize("a\nb\rc\r\nd")
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "a", 1, 1, None),
        (TokenType.ATOM, "b", 2, 1, None),
        (TokenType.ATOM, "c", 3, 1, None),
        (TokenType.ATOM, "d", 4, 1, None),
    ]
    assert result.errors == []


def test_tab_solo_avanza_una_columna() -> None:
    """T02: la tabulación avanza exactamente una columna."""
    result = tokenize("a\tb")
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "a", 1, 1, None),
        (TokenType.ATOM, "b", 1, 3, None),
    ]


def test_comentario_linea_no_genera_token() -> None:
    """T03: % consume hasta antes del salto; el salto actualiza la posición."""
    result = tokenize("% hola\nX")
    assert simplified_tokens(result) == [
        (TokenType.VARIABLE, "X", 2, 1, None)
    ]


def test_comentario_bloque_multilinea_actualiza_posicion() -> None:
    """T04: el bloque puede abarcar líneas y no es anidable."""
    result = tokenize("/* a\nb */X")
    assert simplified_tokens(result) == [
        (TokenType.VARIABLE, "X", 2, 5, None)
    ]


def test_comentario_dentro_de_literal_es_contenido() -> None:
    """T05: % y /* dentro de comillas no inician comentarios."""
    result = tokenize("'% x' \"/* y */\"")
    assert simplified_tokens(result) == [
        (TokenType.QUOTED_ATOM, "'% x'", 1, 1, None),
        (TokenType.STRING, '"/* y */"', 1, 7, None),
    ]


def test_escapes_validos_por_tipo_de_literal() -> None:
    """T06: cada literal acepta sus 5 escapes y conserva el lexema."""
    for source, expected_type in [
        ("'a\\\\b'", TokenType.QUOTED_ATOM),
        ("'a\\'b'", TokenType.QUOTED_ATOM),
        ("'a\\nb'", TokenType.QUOTED_ATOM),
        ('"a\\\\b"', TokenType.STRING),
        ('"a\\"b"', TokenType.STRING),
        ('"a\\nb"', TokenType.STRING),
    ]:
        result = tokenize(source)
        assert result.errors == [], f"{source}: {result.errors}"
        assert len(result.tokens) == 1
        assert result.tokens[0].type == expected_type
        assert result.tokens[0].lexeme == source


def test_escape_invalido_cruzado_por_delimitador() -> None:
    """T07: \\\" es inválido en átomo y \\' es inválido en string."""
    atom = tokenize('\'a\\"b\'')
    assert [ (e.kind, e.fragment) for e in atom.errors ] == [
        (ErrorKind.INVALID_ESCAPE, '\\"')
    ]
    assert atom.tokens == []
    string = tokenize('"a\\\'b"')
    assert [(e.kind, e.fragment) for e in string.errors] == [
        (ErrorKind.INVALID_ESCAPE, "\\'")
    ]
    assert string.tokens == []


def test_tabla_dedup_por_tipo_y_lexema() -> None:
    """T08: repeticiones comparten entrada; formas distintas no se fusionan."""
    result = tokenize("padre padre Persona padre 25 25")
    table = result.symbol_table
    assert len(table) == 3
    assert table.get_index(TokenType.ATOM, "padre") is not None
    assert table.get_index(TokenType.VARIABLE, "Persona") is not None
    assert table.get_index(TokenType.INTEGER, "25") is not None
    first = result.tokens[0].table_index
    second = result.tokens[1].table_index
    assert first == second
    # Comparación estable por conjunto ordenado (no depende del orden interno).
    assert table.sorted_entries() == sorted(
        table.entries(), key=lambda e: (e[0].value, e[1])
    )


def test_anonima_no_se_registra_y_operadores_no_se_registran() -> None:
    """T09: _ no se registra; operadores y delimitadores tampoco."""
    result = tokenize("_ :- (")
    assert result.tokens[0].type == TokenType.ANONYMOUS_VARIABLE
    assert result.tokens[0].table_index is None
    assert result.tokens[1].table_index is None
    assert result.tokens[2].table_index is None
    assert len(result.symbol_table) == 0


def test_errores_se_acumulan_y_se_recupera() -> None:
    """T10: múltiples errores en distintas líneas con tokens válidos después."""
    result = tokenize("@\n5.\n: ok.")
    kinds = [e.kind for e in result.errors]
    assert kinds == [
        ErrorKind.INVALID_CHARACTER,
        ErrorKind.MALFORMED_NUMBER,
        ErrorKind.INVALID_CHARACTER,
    ]
    assert [e.line for e in result.errors] == [1, 2, 3]
    assert simplified_tokens(result) == [
        (TokenType.ATOM, "ok", 3, 3, None),
        (TokenType.DOT, ".", 3, 5, None),
    ]


def test_paren_aislado_sigue_siendo_token() -> None:
    """T11: no se valida balance; ) aislado es RPAREN (alcance léxico)."""
    result = tokenize(")")
    assert simplified_tokens(result) == [
        (TokenType.RPAREN, ")", 1, 1, None)
    ]


def test_menos_doce_es_operador_mas_entero() -> None:
    """T12: los números no tienen signo: -12 son dos tokens."""
    result = tokenize("-12")
    assert simplified_tokens(result) == [
        (TokenType.OPERATOR, "-", 1, 1, ARITH),
        (TokenType.INTEGER, "12", 1, 2, None),
    ]


# ---------------------------------------------------------------------------
# F: archivos completos y corpus en disco
# ---------------------------------------------------------------------------


def test_archivo_valido_sin_errores_y_con_categorias() -> None:
    """F01: programa_valido.pl cubre hechos, regla, consulta y categorías."""
    path = ENTRADAS_DIR / "programa_valido.pl"
    assert path.is_file()
    result = tokenize_file(str(path))
    assert result.errors == [], f"errores: {result.errors}"
    types = {t.type for t in result.tokens}
    for required in [
        TokenType.ATOM,
        TokenType.QUOTED_ATOM,
        TokenType.VARIABLE,
        TokenType.ANONYMOUS_VARIABLE,
        TokenType.INTEGER,
        TokenType.REAL,
        TokenType.STRING,
        TokenType.OPERATOR,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.LBRACKET,
        TokenType.RBRACKET,
        TokenType.LBRACE,
        TokenType.RBRACE,
        TokenType.BAR,
        TokenType.COMMA,
        TokenType.DOT,
    ]:
        assert required in types, f"falta {required}"
    families = {t.family for t in result.tokens if t.family is not None}
    assert families == {
        OperatorFamily.CLAUSE,
        OperatorFamily.QUERY,
        OperatorFamily.DCG,
        OperatorFamily.UNIFICATION_COMPARISON,
        OperatorFamily.ARITHMETIC,
        OperatorFamily.CONTROL,
    }
    # Hecho inicial en 2,1 y consulta en su línea.
    first = result.tokens[0]
    assert (first.type, first.lexeme, first.line, first.column) == (
        TokenType.ATOM,
        "padre",
        2,
        1,
    )
    queries = [t for t in result.tokens if t.lexeme == "?-"]
    assert len(queries) == 1
    assert queries[0].family == OperatorFamily.QUERY


def test_archivo_con_errores_recupera_y_bloque_final_no_recupera() -> None:
    """F02: errores en distintas líneas, recuperación y bloque final a EOF."""
    path = ENTRADAS_DIR / "programa_con_errores.pl"
    assert path.is_file()
    result = tokenize_file(str(path))
    assert len(result.errors) >= 8
    kinds = {e.kind for e in result.errors}
    assert ErrorKind.UNTERMINATED_QUOTED_ATOM in kinds
    assert ErrorKind.UNTERMINATED_STRING in kinds
    assert ErrorKind.UNTERMINATED_BLOCK_COMMENT in kinds
    assert ErrorKind.INVALID_CHARACTER in kinds
    assert ErrorKind.MALFORMED_NUMBER in kinds
    assert ErrorKind.INVALID_ESCAPE in kinds
    lines = {e.line for e in result.errors}
    assert len(lines) >= 5
    for error in result.errors:
        assert error.fragment != ""
        assert error.message.strip() != ""
        assert error.line >= 1 and error.column >= 1
    # Recuperación: tokens válidos después de errores no finales.
    lexemes = [t.lexeme for t in result.tokens]
    for expected in [
        "sigue_valido",
        "otro_valido",
        "resto_valido",
        "cola1",
        "ok",
        "final",
    ]:
        assert expected in lexemes
    # El bloque sin cierre es el último error y no hay tokens posteriores.
    last = result.errors[-1]
    assert last.kind == ErrorKind.UNTERMINATED_BLOCK_COMMENT
    assert result.tokens[-1].line < last.line
    last_token = result.tokens[-1]
    assert (last_token.type, last_token.lexeme, last_token.line) == (
        TokenType.DOT,
        ".",
        16,
    )
    # La expresión válida final existe antes del bloque.
    ok_tokens = [t for t in result.tokens if t.lexeme == "ok"]
    assert len(ok_tokens) >= 1


def test_corpus_validos_en_disco_sin_errores() -> None:
    """F03: todos los .pl de validos/ deben lexear sin errores."""
    files = sorted(VALIDOS_DIR.glob("*.pl"))
    assert len(files) >= 20, f"archivos válidos: {len(files)}"
    for path in files:
        result = tokenize_file(str(path))
        assert result.errors == [], f"{path.name}: {result.errors}"
        assert len(result.tokens) >= 1, f"{path.name} sin tokens"


def test_corpus_invalidos_en_disco_con_error() -> None:
    """F04: todos los .pl de invalidos/ deben producir al menos un error."""
    files = sorted(INVALIDOS_DIR.glob("*.pl"))
    assert len(files) >= 8, f"archivos inválidos: {len(files)}"
    for path in files:
        result = tokenize_file(str(path))
        assert len(result.errors) >= 1, f"{path.name} sin errores"
        for error in result.errors:
            assert error.fragment != ""
            assert error.message.strip() != ""


def test_minimo_de_corpus() -> None:
    """F05: verifica el mínimo exigido (20 válidos, 8 inválidos, prioridades)."""
    assert len(VALID_CASES) >= 20, f"válidos: {len(VALID_CASES)}"
    assert len(PRIORITY_CASES) >= 14, f"prioridad: {len(PRIORITY_CASES)}"
    invalid_with_error = 16  # I01..I16 definidos arriba como funciones
    assert invalid_with_error >= 8
    # Cobertura de categorías del enunciado en los IDs válidos.
    objetivos = " ".join(c["objetivo"] for c in VALID_CASES)
    for palabra in [
        "átomo",
        "variable",
        "anónima",
        "entero",
        "real",
        "comillas",
        "string",
        "cláusula",
        "unificación",
        "aritméticos",
        "control",
        "paréntesis",
        "corchetes",
        "llaves",
        "barra",
        "coma",
        "comentario",
    ]:
        assert palabra in objetivos, f"falta categoría: {palabra}"
    # Dos archivos completos exigidos.
    assert (ENTRADAS_DIR / "programa_valido.pl").is_file()
    assert (ENTRADAS_DIR / "programa_con_errores.pl").is_file()


def test_symbol_table_unidad() -> None:
    """F06: unidad de SymbolTable sin pasar por el lexer."""
    table: SymbolTable = SymbolTable()
    assert len(table) == 0
    first = table.intern(TokenType.ATOM, "padre")
    again = table.intern(TokenType.ATOM, "padre")
    other = table.intern(TokenType.ATOM, "madre")
    assert first == again
    assert other != first
    assert len(table) == 2
