"""Action and ActionEdge Repositories."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.action import Action, ActionEdge
from app.repositories.base import BaseRepository


class ActionRepository(BaseRepository[Action]):
    """Repository for Action persistence operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Action, session)

    async def get_action_for_tenant(
        self, action_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Action | None:
        """Fetch an action strictly scoped to a tenant."""
        stmt = select(Action).where(Action.id == action_id, Action.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_tenant(
        self, tenant_id: uuid.UUID, offset: int = 0, limit: int = 50
    ) -> list[Action]:
        """List actions scoped to a tenant."""
        stmt = select(Action).where(Action.tenant_id == tenant_id).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())


class ActionEdgeRepository(BaseRepository[ActionEdge]):
    """Repository for Action Graph operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ActionEdge, session)

    async def get_edge(
        self, source_id: uuid.UUID, target_id: uuid.UUID, relation_type: str
    ) -> ActionEdge | None:
        """Fetch an exact edge."""
        stmt = select(ActionEdge).where(
            ActionEdge.source_id == source_id,
            ActionEdge.target_id == target_id,
            ActionEdge.relation_type == relation_type,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_dependencies_for_action(
        self, action_id: uuid.UUID, relation_type: str, offset: int = 0, limit: int = 50
    ) -> list[ActionEdge]:
        """Get edges where action_id is the source (i.e. it depends on the targets)."""
        stmt = select(ActionEdge).where(
            ActionEdge.source_id == action_id, ActionEdge.relation_type == relation_type
        ).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_dependents_for_action(
        self, action_id: uuid.UUID, relation_type: str, offset: int = 0, limit: int = 50
    ) -> list[ActionEdge]:
        """Get edges where action_id is the target (i.e. sources that depend on this action)."""
        stmt = select(ActionEdge).where(
            ActionEdge.target_id == action_id, ActionEdge.relation_type == relation_type
        ).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
