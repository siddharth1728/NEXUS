"""API endpoints for Execution Engine."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db_session
from app.core.execution.agent_registry import AgentRegistry
from app.core.execution.policy import PolicyEngine
from app.core.execution.tool_registry import ToolRegistry
from app.core.execution.tools.simulate import SimulatedTool
from app.models.enums import Capability
from app.schemas.agent import Agent
from app.schemas.execution import (
    DryRunResult,
    ExecutionApproval,
    ExecutionRequestCreate,
    ExecutionResponse,
)
from app.services.execution_service import ExecutionService

router = APIRouter()


# In a real app, these registries would be singletons loaded on startup.
# For phase 02B, we inline instantiation in the dependency.
def get_execution_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ExecutionService:
    agent_registry = AgentRegistry()
    # Register mock agents
    agent_registry.register(Agent(
        id="planner",
        name="Planner",
        description="Creates action plans.",
        capabilities=[Capability.ACTION_CREATE, Capability.ACTION_UPDATE]
    ))
    agent_registry.register(Agent(
        id="simulator",
        name="Simulator",
        description="Safe agent for testing.",
        capabilities=[Capability.SYSTEM_SIMULATE]
    ))

    tool_registry = ToolRegistry()
    # Register tools
    tool_registry.register(SimulatedTool())

    policy_engine = PolicyEngine()

    return ExecutionService(
        session=session,
        agent_registry=agent_registry,
        tool_registry=tool_registry,
        policy_engine=policy_engine
    )


@router.post("/", response_model=ExecutionResponse, status_code=status.HTTP_201_CREATED)
async def request_execution(
    request: ExecutionRequestCreate,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[ExecutionService, Depends(get_execution_service)],
) -> ExecutionResponse:
    """Submit a request for an agent to execute a capability via a tool."""
    try:
        # Dummy requester ID, normally extracted from user JWT
        # If user auth is available, pass user ID
        return await service.create_request(str(tenant_id), None, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/dry-run", response_model=DryRunResult)
async def dry_run_execution(
    request: ExecutionRequestCreate,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[ExecutionService, Depends(get_execution_service)],
) -> DryRunResult:
    """Evaluate an execution request policy without committing it to the database."""
    return await service.dry_run(str(tenant_id), request)


@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: uuid.UUID,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[ExecutionService, Depends(get_execution_service)],
) -> ExecutionResponse:
    """Fetch the status of an execution."""
    result = await service.get_execution(str(tenant_id), str(execution_id))
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found.")
    return result


@router.post("/{execution_id}/approve", response_model=ExecutionResponse)
async def approve_execution(
    execution_id: uuid.UUID,
    review: ExecutionApproval,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[ExecutionService, Depends(get_execution_service)],
) -> ExecutionResponse:
    """Human/system approval for AWAITING_APPROVAL executions."""
    try:
        # In a real app we'd pass the current user UUID
        # We mock it for the demo
        dummy_approver = str(tenant_id) # Just an ID
        return await service.review_execution(str(tenant_id), dummy_approver, str(execution_id), review)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{execution_id}/execute", response_model=ExecutionResponse)
async def run_execution(
    execution_id: uuid.UUID,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[ExecutionService, Depends(get_execution_service)],
) -> ExecutionResponse:
    """Trigger the actual execution of an AUTHORIZED request."""
    try:
        return await service.execute(str(tenant_id), str(execution_id))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
