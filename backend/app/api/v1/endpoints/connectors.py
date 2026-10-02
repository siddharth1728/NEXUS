from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

import uuid
from app.api.deps import get_db_session, get_current_tenant_id
from app.core.execution.connectors.registry import connector_registry
from app.schemas.connection import Connection as ConnectionSchema, ConnectionCreate, ConnectorHealth, ConnectionStatus
from app.services.connection_service import ConnectionService
from app.core.execution.tool import ExecutionContext
from app.core.errors import UnauthorizedError

router = APIRouter()

@router.get("/", response_model=List[str])
async def list_connectors() -> List[str]:
    """List all available connector providers."""
    return connector_registry.list_all()

@router.post("/{provider}/connect", response_model=ConnectionSchema)
async def connect_provider(
    provider: str,
    connection_in: dict[str, Any],
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    session: AsyncSession = Depends(get_db_session),
) -> ConnectionSchema:
    """Create or update a connection metadata for a provider."""
    if provider not in connector_registry.list_all():
        raise HTTPException(status_code=404, detail="Provider not found in registry")
        
    connection_service = ConnectionService(session)
    # The actual credentials should be stored via SecretStore, NOT in metadata
    connection = await connection_service.create_or_update_connection(
        tenant_id=str(tenant_id),
        provider=provider,
        status=ConnectionStatus.AVAILABLE,
        metadata=connection_in,
        user_id=None
    )
    return connection

@router.get("/{provider}/health", response_model=ConnectorHealth)
async def check_connector_health(
    provider: str,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    session: AsyncSession = Depends(get_db_session),
) -> ConnectorHealth:
    """Check the health of a specific provider connection."""
    if provider not in connector_registry.list_all():
        raise HTTPException(status_code=404, detail="Provider not found in registry")
        
    connection_service = ConnectionService(session)
    connection = await connection_service.get_connection(tenant_id=str(tenant_id), provider=provider)
    if not connection:
        raise HTTPException(status_code=400, detail="Connection required")
        
    connector = connector_registry.get(provider)
    context = ExecutionContext(tenant_id=str(tenant_id), user_id=None)
    
    try:
        health_status = await connector.check_health(connection)
        return health_status
    except UnauthorizedError:
        return ConnectorHealth(
            status=ConnectionStatus.AUTHENTICATION_REQUIRED,
            provider=provider,
            message="Authentication required",
            last_checked=connection.updated_at
        )
    except Exception as e:
        return ConnectorHealth(
            status=ConnectionStatus.UNAVAILABLE,
            provider=provider,
            message=str(e),
            last_checked=connection.updated_at
        )
