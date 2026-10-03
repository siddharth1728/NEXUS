"""API endpoints for autonomous loop execution."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db_session
from app.api.v1.endpoints.execution import get_execution_service
from app.models.enums import AutonomyMode
from app.services.action_service import ActionService
from app.services.autonomous_loop_service import AutonomousLoopService
from app.services.execution_service import ExecutionService
from app.services.verification_service import VerificationService
from app.services.workflow_service import WorkflowEngine

router = APIRouter()


@router.post("/run", response_model=dict[str, Any])
async def run_autonomous_loop(
    mode: AutonomyMode = Query(default=AutonomyMode.AUTONOMOUS_WITHIN_POLICY),
    max_iterations: int = Query(default=5, le=20),
    tenant_id: uuid.UUID = Depends(get_current_tenant_id),
    db: AsyncSession = Depends(get_db_session),
    execution_service: ExecutionService = Depends(get_execution_service),
) -> dict[str, Any]:
    """Run the autonomous loop for the current tenant."""
    action_service = ActionService(db)
    loop_service = AutonomousLoopService(
        db=db,
        action_service=action_service,
        execution_service=execution_service,
        verification_service=VerificationService(db, execution_service.tool_registry),
        workflow_engine=WorkflowEngine(db, action_service),
    )


    result = await loop_service.run_loop(
        tenant_id=tenant_id,
        mode=mode,
        max_iterations=max_iterations,
    )

    return result

