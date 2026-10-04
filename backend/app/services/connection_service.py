"""Connection Service."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.connection import Connection
from app.schemas.connection import Connection as ConnectionSchema
from app.schemas.connection import ConnectionStatus


class ConnectionService:
    """Service for managing external provider connections."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_connection(self, tenant_id: str, provider: str) -> ConnectionSchema | None:
        """Retrieve a connection by tenant and provider."""
        stmt = select(Connection).where(
            Connection.tenant_id == tenant_id,
            Connection.provider == provider
        )
        result = await self.session.execute(stmt)
        connection = result.scalar_one_or_none()
        if not connection:
            return None
        return ConnectionSchema.model_validate(connection)

    async def list_connections(self, tenant_id: str) -> list[ConnectionSchema]:
        """List all connections for a tenant."""
        stmt = select(Connection).where(Connection.tenant_id == tenant_id)
        result = await self.session.execute(stmt)
        connections = result.scalars().all()
        return [ConnectionSchema.model_validate(c) for c in connections]

    async def create_or_update_connection(
        self, tenant_id: str, provider: str, status: ConnectionStatus, metadata: dict[str, Any], user_id: str | None = None
    ) -> ConnectionSchema:
        """Create or update a connection record.

        Credentials must NEVER be passed in the metadata field.
        """
        stmt = select(Connection).where(
            Connection.tenant_id == tenant_id,
            Connection.provider == provider
        )
        result = await self.session.execute(stmt)
        connection = result.scalar_one_or_none()

        if connection:
            connection.status = status.value
            connection.connection_metadata = metadata
            if user_id:
                connection.user_id = user_id
        else:
            connection = Connection(
                id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                user_id=user_id,
                provider=provider,
                status=status.value,
                connection_metadata=metadata,
            )
            self.session.add(connection)

        await self.session.commit()
        await self.session.refresh(connection)
        return ConnectionSchema.model_validate(connection)
