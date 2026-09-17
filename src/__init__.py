"""API pública del analizador léxico."""

from .errors import LexicalError, LexicalErrorKind
from .lexer import Lexer
from .symbol_table import LexemeEntry, SymbolTable
from .tokens import Token, TokenType

__all__ = [
    "LexemeEntry",
    "Lexer",
    "LexicalError",
    "LexicalErrorKind",
    "SymbolTable",
    "Token",
    "TokenType",
]
