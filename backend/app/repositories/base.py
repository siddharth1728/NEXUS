"""NEXUS Base Repository Abstraction.

Defines generic asynchronous repository contracts for database CRUD operations.
"""

import uuid
from typing import Any, Generic, TypeVar

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic async repository providing CRUD operations for SQLAlchemy models."""

    def __init__(self, model: type[ModelType], session: AsyncSession) -> None:
        self.model = model
        self.session = session

    async def get_by_id(self, id_: uuid.UUID) -> ModelType | None:
        """Fetch a single record by primary key UUID."""
        return await self.session.get(self.model, id_)

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 50,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """List records with pagination and optional attribute equality filters."""
        stmt = select(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """Count records matching optional filters."""
        stmt = select(func.count()).select_from(self.model)
        if filters:
            for field, value in filters.items():
                if hasattr(self.model, field):
                    stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def create(self, instance: ModelType) -> ModelType:
        """Persist a new model instance."""
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def delete_by_id(self, id_: uuid.UUID) -> bool:
        """Delete record by primary key UUID."""
        stmt = delete(self.model).where(self.model.id == id_)  # type: ignore[attr-defined]
        result = await self.session.execute(stmt)
        rowcount = getattr(result, "rowcount", 0) or 0
        return rowcount > 0
