"""API pública del analizador léxico."""

from .errors import ErrorKind, LexError, LexicalError, LexicalErrorKind
from .lexer import LexResult, Lexer, tokenize, tokenize_file
from .symbol_table import LexemeEntry, SymbolTable
from .tokens import OperatorFamily, Token, TokenType

__all__ = [
    "ErrorKind",
    "LexemeEntry",
    "LexError",
    "LexResult",
    "Lexer",
    "LexicalError",
    "LexicalErrorKind",
    "OperatorFamily",
    "SymbolTable",
    "Token",
    "TokenType",
    "tokenize",
    "tokenize_file",
]
