"""Action Endpoints."""

import uuid

import fastapi
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db_session
from app.schemas.action import (
    ActionCreate,
    ActionEdgeCreate,
    ActionEdgeResponse,
    ActionResponse,
    ActionStateTransition,
    ActionUpdate,
)
from app.services.action_service import ActionService

router = APIRouter()


def get_action_service(session: AsyncSession = Depends(get_db_session)) -> ActionService:
    return ActionService(session)


@router.post("", response_model=ActionResponse, status_code=status.HTTP_201_CREATED)
async def create_action(
    data: ActionCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> ActionResponse:
    """Create a new action for the current tenant."""
    action = await service.create_action(tenant_id, data)
    await service.session.commit()
    return ActionResponse.model_validate(action)


@router.get("", response_model=list[ActionResponse])
async def list_actions(
    response: fastapi.Response,
    offset: int = 0,
    limit: int = 50,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> list[ActionResponse]:
    """List actions for the current tenant."""
    actions, total = await service.list_actions(tenant_id, offset=offset, limit=limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Total-Pages"] = str((total + limit - 1) // limit if limit > 0 else 1)
    response.headers["X-Current-Page"] = str((offset // limit) + 1 if limit > 0 else 1)
    response.headers["X-Per-Page"] = str(limit)
    return [ActionResponse.model_validate(a) for a in actions]


@router.get("/{action_id}", response_model=ActionResponse)
async def get_action(
    action_id: uuid.UUID,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> ActionResponse:
    """Get a specific action by ID."""
    action = await service.get_action(action_id, tenant_id)
    return ActionResponse.model_validate(action)


@router.patch("/{action_id}", response_model=ActionResponse)
async def update_action(
    action_id: uuid.UUID,
    data: ActionUpdate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> ActionResponse:
    """Update action metadata."""
    action = await service.update_action(action_id, tenant_id, data)
    await service.session.commit()
    return ActionResponse.model_validate(action)


@router.post("/{action_id}/transition", response_model=ActionResponse)
async def transition_action(
    action_id: uuid.UUID,
    data: ActionStateTransition,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> ActionResponse:
    """Transition an action's state."""
    action = await service.transition_state(action_id, tenant_id, data.new_status)
    await service.session.commit()
    return ActionResponse.model_validate(action)


@router.post(
    "/{action_id}/dependencies",
    response_model=ActionEdgeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_dependency(
    action_id: uuid.UUID,
    data: ActionEdgeCreate,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> ActionEdgeResponse:
    """Create a dependency edge originating from this action."""
    edge = await service.create_dependency(
        tenant_id=tenant_id,
        source_id=action_id,
        target_id=data.target_id,
        relation_type=data.relation_type,
        metadata=data.metadata_payload,
    )
    await service.session.commit()
    return ActionEdgeResponse.model_validate(edge)


@router.get("/{action_id}/dependencies", response_model=list[ActionEdgeResponse])
async def get_dependencies(
    action_id: uuid.UUID,
    response: fastapi.Response,
    offset: int = 0,
    limit: int = 50,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> list[ActionEdgeResponse]:
    """Get edges where this action is the source."""
    edges, total = await service.get_dependencies(action_id, tenant_id, offset, limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Total-Pages"] = str((total + limit - 1) // limit if limit > 0 else 1)
    response.headers["X-Current-Page"] = str((offset // limit) + 1 if limit > 0 else 1)
    response.headers["X-Per-Page"] = str(limit)
    return [ActionEdgeResponse.model_validate(e) for e in edges]


@router.get("/{action_id}/dependents", response_model=list[ActionEdgeResponse])
async def get_dependents(
    action_id: uuid.UUID,
    response: fastapi.Response,
    offset: int = 0,
    limit: int = 50,
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    service: ActionService = Depends(get_action_service),
) -> list[ActionEdgeResponse]:
    """Get edges where this action is the target."""
    edges, total = await service.get_dependents(action_id, tenant_id, offset, limit)
    response.headers["X-Total-Count"] = str(total)
    response.headers["X-Total-Pages"] = str((total + limit - 1) // limit if limit > 0 else 1)
    response.headers["X-Current-Page"] = str((offset // limit) + 1 if limit > 0 else 1)
    response.headers["X-Per-Page"] = str(limit)
    return [ActionEdgeResponse.model_validate(e) for e in edges]
