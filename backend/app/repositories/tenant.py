"""Tenant Repository."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.tenant import Tenant
from app.repositories.base import BaseRepository


class TenantRepository(BaseRepository[Tenant]):
    """Repository for Tenant persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Tenant, session)

    async def get_by_name(self, name: str) -> Tenant | None:
        """Fetch a tenant by exact name match."""
        stmt = select(Tenant).where(Tenant.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
