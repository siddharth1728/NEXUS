from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.database import get_db
from app.models.user import User
from app.dependencies.auth import get_current_user
from app.schemas.copilot import (
    CopilotAskRequest,
    CopilotAskResponse,
    InterviewStartRequest,
    InterviewStartResponse,
    InterviewAnswerRequest,
    InterviewAnswerResponse,
)
from app.services.copilot_service import (
    ask_copilot,
    start_interview_session,
    submit_interview_answer,
    build_verified_context_package
)
from app.services import telemetry_service

router = APIRouter(prefix="/api/copilot", tags=["AI Copilot & Defend Your Build"])

@router.post("/ask", response_model=CopilotAskResponse)
def ask_copilot_endpoint(
    payload: CopilotAskRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Answers natural language engineering questions grounded strictly in verified NEXUS context."""
    try:
        result = ask_copilot(
            db=db,
            user_id=current_user.id,
            query=payload.query,
            project_id=payload.project_id,
            concept_key=payload.concept_key,
            skill_name=payload.skill_name
        )
        telemetry_service.record_event(db, "COPILOT_STARTED", user_id=current_user.id, context={"project_id": payload.project_id})
        return result
    except Exception as e:
        telemetry_service.record_event(db, "AI_FAILURE", user_id=current_user.id, context={"operation": "ask_copilot", "error": str(e)})
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Copilot processing failed: {str(e)}"
        )

@router.post("/interview/start", response_model=InterviewStartResponse)
def start_interview_endpoint(
    payload: InterviewStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiates a grounded 'Defend Your Build' technical interview session for a user project."""
    try:
        session = start_interview_session(
            db=db,
            user_id=current_user.id,
            project_id=payload.project_id,
            difficulty=payload.difficulty
        )
        telemetry_service.record_event(db, "DEFEND_BUILD_STARTED", user_id=current_user.id, context={"project_id": payload.project_id, "session_id": session.session_id})
        return session
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        telemetry_service.record_event(db, "AI_FAILURE", user_id=current_user.id, context={"operation": "start_interview", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/interview/answer", response_model=InterviewAnswerResponse)
def submit_answer_endpoint(
    payload: InterviewAnswerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Evaluates the student's answer and provides structured coaching feedback and next question."""
    try:
        response = submit_interview_answer(
            db=db,
            user_id=current_user.id,
            session_id=payload.session_id,
            answer=payload.answer
        )
        if response.is_finished:
            telemetry_service.record_event(db, "DEFEND_BUILD_COMPLETED", user_id=current_user.id, context={"session_id": payload.session_id})
        return response
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        telemetry_service.record_event(db, "AI_FAILURE", user_id=current_user.id, context={"operation": "submit_interview_answer", "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/context/{project_id}")
def get_verified_context_endpoint(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Returns the sanitized verified context package assembled for the project."""
    pkg = build_verified_context_package(db, current_user.id, project_id)
    return pkg
