from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.core.config import settings
from app.services import telemetry_service

router = APIRouter(prefix="/api/telemetry", tags=["Telemetry"])

class EventCreate(BaseModel):
    event_type: str
    context: Optional[dict] = None

class FeedbackCreate(BaseModel):
    feature_context: str
    is_helpful: bool
    reason: Optional[str] = None

def get_internal_user(current_user: User = Depends(get_current_user)):
    """Dependency to enforce internal access control for health endpoints."""
    if not current_user.is_internal:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: Internal role required"
        )
    return current_user

@router.post("/event", status_code=202)
def report_event(
    event_data: EventCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint for frontend to report lightweight telemetry events.
    Execution is offloaded to a background task to prevent UX latency.
    """
    background_tasks.add_task(
        telemetry_service.record_event,
        db=db,
        event_type=event_data.event_type,
        user_id=current_user.id,
        context=event_data.context
    )
    return {"status": "accepted"}

@router.post("/feedback", status_code=201)
def submit_feedback(
    feedback_data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit contextual product feedback.
    """
    telemetry_service.record_feedback(
        db=db,
        user_id=current_user.id,
        feature_context=feedback_data.feature_context,
        is_helpful=feedback_data.is_helpful,
        reason=feedback_data.reason
    )
    return {"message": "Feedback recorded"}

@router.get("/config/flags")
def get_feature_flags():
    """
    Publicly safe endpoint to check which UI features are enabled.
    """
    return {
        "ai_copilot": settings.ENABLE_AI_COPILOT,
        "proof_quests": settings.ENABLE_PROOF_QUESTS,
        "engineering_lab": settings.ENABLE_ENGINEERING_LAB,
        "nexus_id": settings.ENABLE_NEXUS_ID
    }

@router.get("/internal/health", dependencies=[Depends(get_internal_user)])
def internal_product_health(db: Session = Depends(get_db)):
    """
    Internal-only endpoint to view aggregate product health metrics.
    Requires is_internal = True on the authenticated user.
    """
    return telemetry_service.get_product_health(db)
