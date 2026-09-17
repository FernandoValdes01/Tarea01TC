"""Tabla de lexemas: estructura léxica sin información semántica.

Contrato: docs/informe/01_especificacion_lexica.md, sección 10.
Se registran ATOM, QUOTED_ATOM, VARIABLE, INTEGER, REAL y STRING con clave
(tipo, lexema original). ANONYMOUS_VARIABLE, operadores, delimitadores,
espacios y comentarios no se registran.
"""

from __future__ import annotations

from .tokens import TokenType


class SymbolTable:
    """Deduplica lexemas por (tipo, lexema original)."""

    def __init__(self) -> None:
        self._index: dict[tuple[TokenType, str], int] = {}
        self._entries: list[tuple[TokenType, str]] = []

    def intern(self, token_type: TokenType, lexeme: str) -> int:
        """Registra o reutiliza la entrada y retorna su índice léxico."""
        key = (token_type, lexeme)
        existing = self._index.get(key)
        if existing is not None:
            return existing
        idx = len(self._entries)
        self._index[key] = idx
        self._entries.append(key)
        return idx

    def get_index(self, token_type: TokenType, lexeme: str) -> int | None:
        """Retorna el índice o None si no existe."""
        return self._index.get((token_type, lexeme))

    def entries(self) -> list[tuple[TokenType, str]]:
        """Entradas en orden de inserción (orden no contractual)."""
        return list(self._entries)

    def sorted_entries(self) -> list[tuple[TokenType, str]]:
        """Entradas ordenadas por (tipo, lexema) para comparaciones estables."""
        return sorted(self._entries, key=lambda e: (e[0].value, e[1]))

    def __len__(self) -> int:
        return len(self._entries)

    def __contains__(self, key: object) -> bool:
        return key in self._index
