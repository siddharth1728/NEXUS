"""API endpoints for Action Synthesis."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_tenant_id, get_db_session
from app.core.ai.gateway import AIGateway
from app.schemas.action import ActionResponse
from app.schemas.synthesis import (
    CandidateAction,
    CandidateActionValidationResult,
    SynthesisContext,
    SynthesisResult,
)
from app.services.action_service import ActionService
from app.services.synthesis_service import SynthesisService

router = APIRouter()


def get_synthesis_service(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> SynthesisService:
    return SynthesisService(
        ai_gateway=AIGateway(), action_service=ActionService(session)
    )


@router.post("/synthesize", response_model=SynthesisResult)
async def synthesize_actions(
    context: SynthesisContext,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[SynthesisService, Depends(get_synthesis_service)],
) -> SynthesisResult:
    """
    Synthesize candidate actions from the provided extraction context.
    Returns AI proposals that are not yet persisted as Actions.
    """
    # Enforce tenant isolation for the context
    if context.tenant_id != tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch in synthesis context.",
        )

    return await service.synthesize(context)


@router.post("/validate", response_model=CandidateActionValidationResult)
async def validate_candidate(
    candidate: CandidateAction,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[SynthesisService, Depends(get_synthesis_service)],
) -> CandidateActionValidationResult:
    """
    Inspect and validate a candidate action without persisting it.
    """
    return await service.validate_candidate(candidate, str(tenant_id))


@router.post("/create-action", response_model=ActionResponse)
async def create_action_from_candidate(
    candidate: CandidateAction,
    tenant_id: Annotated[uuid.UUID, Depends(get_current_tenant_id)],
    service: Annotated[SynthesisService, Depends(get_synthesis_service)],
) -> ActionResponse:
    """
    Convert an approved candidate into a persisted Action.
    """
    try:
        action = await service.create_action_from_candidate(str(tenant_id), candidate)
        return action
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
