"""Vector type compatibility layer for SQLAlchemy.

Uses pgvector on PostgreSQL, falls back to JSON (as list of floats) on SQLite.
"""

from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON
from sqlalchemy.types import TypeDecorator


class HybridVector(TypeDecorator):
    """
    A custom SQLAlchemy type for vector embeddings.
    Compiles to pgvector's VECTOR(dim) in PostgreSQL.
    Compiles to JSON in SQLite.
    """
    impl = JSON
    cache_ok = True

    def __init__(self, dim: int, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim

    def load_dialect_impl(self, dialect: Any) -> Any:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(Vector(self.dim))
        else:
            return dialect.type_descriptor(JSON(none_as_null=True))

    def process_bind_param(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        return list(value)

    def process_result_value(self, value: Any, dialect: Any) -> Any:
        if value is None:
            return value
        if isinstance(value, str):
            import json
            value = json.loads(value)
        return list(value)
