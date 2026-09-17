"""Pruebas del analizador léxico del subconjunto de Prolog."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.errors import LexicalErrorKind
from src.lexer import Lexer
from src.symbol_table import SymbolTable
from src.tokens import Token, TokenType


ROOT = Path(__file__).resolve().parents[1]


class LexerTokenTests(unittest.TestCase):
    def tokenize(self, source: str) -> tuple[Lexer, list[Token]]:
        lexer = Lexer(source)
        return lexer, lexer.tokenize()

    def test_atoms_variables_and_anonymous_variable(self) -> None:
        lexer, tokens = self.tokenize("padre persona_1 X Persona _Temporal _1 _")

        self.assertEqual(
            [token.type for token in tokens],
            [
                TokenType.ATOM,
                TokenType.ATOM,
                TokenType.VARIABLE,
                TokenType.VARIABLE,
                TokenType.VARIABLE,
                TokenType.VARIABLE,
                TokenType.ANONYMOUS_VARIABLE,
            ],
        )
        self.assertEqual(tokens[-1].lexeme, "_")
        self.assertEqual(lexer.errors, [])

    def test_numbers_and_signs(self) -> None:
        lexer, tokens = self.tokenize("0 0007 3.14 -12 +0.5")

        self.assertEqual(
            [(token.type, token.lexeme) for token in tokens],
            [
                (TokenType.INTEGER, "0"),
                (TokenType.INTEGER, "0007"),
                (TokenType.REAL, "3.14"),
                (TokenType.OPERATOR, "-"),
                (TokenType.INTEGER, "12"),
                (TokenType.OPERATOR, "+"),
                (TokenType.REAL, "0.5"),
            ],
        )
        self.assertEqual(lexer.errors, [])

    def test_quoted_literals_keep_raw_text(self) -> None:
        source = "'Juan Pérez' 'it\\'s' \"dice: \\\"sí\\\"\""
        lexer, tokens = self.tokenize(source)

        self.assertEqual(
            [(token.type, token.lexeme) for token in tokens],
            [
                (TokenType.QUOTED_ATOM, "'Juan Pérez'"),
                (TokenType.QUOTED_ATOM, "'it\\'s'"),
                (TokenType.STRING, '"dice: \\"sí\\""'),
            ],
        )
        self.assertEqual(lexer.errors, [])

    def test_all_symbolic_operators_use_maximal_munch(self) -> None:
        source = r"\== \= =.. == =< >= :- ?- // ** \+ --> = < > / + - * ! ;"
        lexer, tokens = self.tokenize(source)

        self.assertEqual(
            [token.lexeme for token in tokens],
            [
                r"\==",
                r"\=",
                "=..",
                "==",
                "=<",
                ">=",
                ":-",
                "?-",
                "//",
                "**",
                r"\+",
                "-->",
                "=",
                "<",
                ">",
                "/",
                "+",
                "-",
                "*",
                "!",
                ";",
            ],
        )
        self.assertTrue(all(token.type is TokenType.OPERATOR for token in tokens))
        self.assertEqual(lexer.errors, [])

    def test_operator_families_and_complete_words(self) -> None:
        lexer, tokens = self.tokenize("is mod isla modulo isX :- ?- --> = + \\+")

        self.assertEqual(
            [(token.type, token.lexeme, token.attribute) for token in tokens],
            [
                (TokenType.OPERATOR, "is", "ARITHMETIC"),
                (TokenType.OPERATOR, "mod", "ARITHMETIC"),
                (TokenType.ATOM, "isla", 0),
                (TokenType.ATOM, "modulo", 1),
                (TokenType.ATOM, "is", 2),
                (TokenType.VARIABLE, "X", 3),
                (TokenType.OPERATOR, ":-", "CLAUSE"),
                (TokenType.OPERATOR, "?-", "QUERY"),
                (TokenType.OPERATOR, "-->", "DCG"),
                (TokenType.OPERATOR, "=", "UNIFICATION_COMPARISON"),
                (TokenType.OPERATOR, "+", "ARITHMETIC"),
                (TokenType.OPERATOR, r"\+", "CONTROL"),
            ],
        )
        self.assertEqual(lexer.errors, [])

    def test_delimiters(self) -> None:
        lexer, tokens = self.tokenize("()[]{}|,.")

        self.assertEqual(
            [token.type for token in tokens],
            [
                TokenType.LPAREN,
                TokenType.RPAREN,
                TokenType.LBRACKET,
                TokenType.RBRACKET,
                TokenType.LBRACE,
                TokenType.RBRACE,
                TokenType.BAR,
                TokenType.COMMA,
                TokenType.DOT,
            ],
        )
        self.assertEqual(lexer.errors, [])

    def test_comments_are_ignored_and_positions_are_preserved(self) -> None:
        source = "% uno\r\n\tX /* dos\n tres */ atom"
        lexer, tokens = self.tokenize(source)

        self.assertEqual(
            [(token.lexeme, token.line, token.column) for token in tokens],
            [("X", 2, 2), ("atom", 3, 10)],
        )
        self.assertEqual(lexer.errors, [])

    def test_symbol_table_deduplicates_by_type_and_exact_lexeme(self) -> None:
        lexer, tokens = self.tokenize('x x X X "x" "x" \'x\' \'x\' 2 2 2.0 2.0 _')

        self.assertEqual(len(lexer.symbol_table), 6)
        self.assertEqual(tokens[0].attribute, tokens[1].attribute)
        self.assertEqual(tokens[2].attribute, tokens[3].attribute)
        self.assertEqual(tokens[-1].type, TokenType.ANONYMOUS_VARIABLE)
        self.assertIsNone(tokens[-1].attribute)
        self.assertEqual(
            [(entry.index, entry.token_type, entry.original_lexeme) for entry in lexer.symbol_table.entries],
            [
                (0, TokenType.ATOM, "x"),
                (1, TokenType.VARIABLE, "X"),
                (2, TokenType.STRING, '"x"'),
                (3, TokenType.QUOTED_ATOM, "'x'"),
                (4, TokenType.INTEGER, "2"),
                (5, TokenType.REAL, "2.0"),
            ],
        )

    def test_token_basic_text_omits_attribute(self) -> None:
        token = Token(TokenType.OPERATOR, ":-", 4, 7, "CLAUSE")

        self.assertEqual(str(token), "<OPERATOR, ':-', 4, 7>")
        self.assertIn("CLAUSE", token.format(include_attribute=True))


class LexerErrorTests(unittest.TestCase):
    def assert_error(self, source: str, kind: LexicalErrorKind, fragment: str) -> Lexer:
        lexer = Lexer(source)
        lexer.tokenize()
        self.assertIn(kind, [error.kind for error in lexer.errors])
        self.assertIn(fragment, [error.fragment for error in lexer.errors])
        return lexer

    def test_malformed_numbers_are_one_error_fragment(self) -> None:
        for source in ("5.", ".5", "1.2.3", "1..2", "12abc"):
            with self.subTest(source=source):
                lexer = self.assert_error(source, LexicalErrorKind.MALFORMED_NUMBER, source)
                self.assertEqual(lexer.tokens, [])

    def test_identifier_suffix_is_consumed_but_trailing_dot_is_safe(self) -> None:
        lexer = Lexer("12abc. X")
        tokens = lexer.tokenize()

        self.assertEqual(
            [(token.type, token.lexeme) for token in tokens],
            [(TokenType.DOT, "."), (TokenType.VARIABLE, "X")],
        )
        self.assertEqual(
            [(error.kind, error.fragment) for error in lexer.errors],
            [(LexicalErrorKind.MALFORMED_NUMBER, "12abc")],
        )

    def test_invalid_characters_recover(self) -> None:
        lexer = Lexer(": ? \\ @ á ok")
        tokens = lexer.tokenize()

        self.assertEqual([token.lexeme for token in tokens], ["ok"])
        self.assertEqual(
            [error.kind for error in lexer.errors],
            [LexicalErrorKind.INVALID_CHARACTER] * 5,
        )

    def test_unterminated_literals_recover_at_newline(self) -> None:
        lexer = Lexer("'sin cierre\nX \"otro\r\nY")
        tokens = lexer.tokenize()

        self.assertEqual([token.lexeme for token in tokens], ["X", "Y"])
        self.assertEqual(
            [error.kind for error in lexer.errors],
            [
                LexicalErrorKind.UNTERMINATED_QUOTED_ATOM,
                LexicalErrorKind.UNTERMINATED_STRING,
            ],
        )
        self.assertEqual([(token.line, token.column) for token in tokens], [(2, 1), (3, 1)])

    def test_invalid_escapes_do_not_emit_literal_token(self) -> None:
        lexer = Lexer("'a\\q\\0' X \"a\\'b\" Y")
        tokens = lexer.tokenize()

        self.assertEqual([token.lexeme for token in tokens], ["X", "Y"])
        self.assertEqual(
            [error.kind for error in lexer.errors],
            [
                LexicalErrorKind.INVALID_ESCAPE,
                LexicalErrorKind.INVALID_ESCAPE,
                LexicalErrorKind.INVALID_ESCAPE,
            ],
        )

    def test_backslash_does_not_hide_a_physical_newline(self) -> None:
        lexer = Lexer('"a\\\nX')
        tokens = lexer.tokenize()

        self.assertEqual([token.lexeme for token in tokens], ["X"])
        self.assertEqual(
            [error.kind for error in lexer.errors],
            [
                LexicalErrorKind.INVALID_ESCAPE,
                LexicalErrorKind.UNTERMINATED_STRING,
            ],
        )
        self.assertEqual((tokens[0].line, tokens[0].column), (2, 1))

    def test_unterminated_block_comment_consumes_to_eof(self) -> None:
        lexer = self.assert_error(
            "X /* sin cierre\nY",
            LexicalErrorKind.UNTERMINATED_BLOCK_COMMENT,
            "/* sin cierre\nY",
        )

        self.assertEqual([token.lexeme for token in lexer.tokens], ["X"])
        self.assertEqual((lexer.line, lexer.column), (2, 2))

    def test_error_text_includes_kind_position_and_fragment(self) -> None:
        lexer = self.assert_error("@", LexicalErrorKind.INVALID_CHARACTER, "@")
        rendered = str(lexer.errors[0])

        self.assertIn("INVALID_CHARACTER", rendered)
        self.assertIn("línea 1, columna 1", rendered)
        self.assertIn("'@'", rendered)


class PublicApiTests(unittest.TestCase):
    def test_custom_symbol_table_can_be_injected(self) -> None:
        table = SymbolTable()
        lexer = Lexer("x", symbol_table=table)

        lexer.tokenize()

        self.assertIs(lexer.symbol_table, table)
        self.assertEqual(len(table), 1)

    def test_cli_prints_recovered_tokens_and_returns_one_on_lexical_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_file = Path(directory) / "entrada.pl"
            source_file.write_text("X @ Y", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "src.main", str(source_file)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 1)
        self.assertIn("<VARIABLE, 'X', 1, 1>", result.stdout)
        self.assertIn("<VARIABLE, 'Y', 1, 5>", result.stdout)
        self.assertIn("Errores léxicos", result.stderr)
        self.assertIn("INVALID_CHARACTER", result.stderr)


if __name__ == "__main__":
    unittest.main()
