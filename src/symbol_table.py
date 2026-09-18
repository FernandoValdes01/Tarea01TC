"""Tabla léxica sin información sintáctica ni semántica."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from .tokens import TokenType


STORED_TOKEN_TYPES = frozenset(
    {
        TokenType.ATOM,
        TokenType.QUOTED_ATOM,
        TokenType.VARIABLE,
        TokenType.INTEGER,
        TokenType.REAL,
        TokenType.STRING,
    }
)


@dataclass(frozen=True, slots=True)
class LexemeEntry:
    """Entrada estable de la tabla de lexemas."""

    index: int
    token_type: TokenType
    normalized_value: str
    original_lexeme: str


class LexemeEntries(tuple[LexemeEntry, ...]):
    """Vista inmutable que también conserva la interfaz ``entries()`` remota."""

    def __call__(self) -> list[tuple[TokenType, str]]:
        return [(entry.token_type, entry.original_lexeme) for entry in self]


class SymbolTable:
    """Deduplica lexemas por categoría y texto exacto.

    El contrato no permite des-escapar, quitar comillas ni normalizar mayúsculas.
    Por eso el valor normalizado es el propio lexema original. La variable
    anónima ``_`` nunca se registra: cada aparición es independiente.
    """

    def __init__(self) -> None:
        self._entries: list[LexemeEntry] = []
        self._indices: dict[tuple[TokenType, str], int] = {}

    @property
    def entries(self) -> LexemeEntries:
        """Vista inmutable de las entradas en orden de inserción."""

        return LexemeEntries(self._entries)

    def register(self, token_type: TokenType, lexeme: str) -> int:
        """Registra un lexema y devuelve su índice estable, desde cero."""

        if token_type is TokenType.ANONYMOUS_VARIABLE:
            raise ValueError("La variable anónima no se registra en la tabla")
        if token_type not in STORED_TOKEN_TYPES:
            raise ValueError(f"{token_type.name} no pertenece a la tabla de lexemas")

        normalized_value = self._normalize(lexeme)
        key = (token_type, normalized_value)
        existing = self._indices.get(key)
        if existing is not None:
            return existing

        index = len(self._entries)
        entry = LexemeEntry(index, token_type, normalized_value, lexeme)
        self._entries.append(entry)
        self._indices[key] = index
        return index

    def get(self, index: int) -> LexemeEntry:
        """Consulta una entrada por su índice."""

        return self._entries[index]

    def intern(self, token_type: TokenType, lexeme: str) -> int:
        """Alias de ``register`` usado por la interfaz funcional."""

        return self.register(token_type, lexeme)

    def get_index(self, token_type: TokenType, lexeme: str) -> int | None:
        """Devuelve el índice existente sin crear una entrada."""

        return self._indices.get((token_type, self._normalize(lexeme)))

    def sorted_entries(self) -> list[tuple[TokenType, str]]:
        """Devuelve pares ordenados para comparaciones reproducibles."""

        return sorted(self.entries(), key=lambda entry: (entry[0].value, entry[1]))

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[LexemeEntry]:
        return iter(self._entries)

    def __contains__(self, key: object) -> bool:
        return key in self._indices

    @staticmethod
    def _normalize(lexeme: str) -> str:
        return lexeme
