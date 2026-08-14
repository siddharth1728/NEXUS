from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database.database import get_db
from app.models.user import User, Gap
from app.models.project import Project
from app.models.action import Recommendation, ActionHistory, ActionHistoryStatus
from app.schemas.action import (
    RecommendationResponse, TraceabilityInfo, ActionPayload,
    ProofQuestSummary, ProofQuestDetail, QuestVerificationResponse
)
from app.dependencies.auth import get_current_user
from app.core.csrf import verify_csrf_token
from app.services.nba_engine import (
    recalculate_next_best_action, get_available_quests,
    get_quest_detail, verify_quest_outcome
)
from app.config.action_catalog import get_action_catalog

router = APIRouter()

# ── 1. Phase 6 Backward Compatible Endpoints ────────────────────────
@router.get("/next-best-action", response_model=RecommendationResponse)
def get_next_best_action(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.query(Recommendation).filter(Recommendation.user_id == current_user.id).first()
    
    if not rec:
        rec = recalculate_next_best_action(current_user.id, db)
        if not rec:
            raise HTTPException(status_code=404, detail="NO_ACTION")
            
    catalog = get_action_catalog()
    action_def = next((a for a in catalog if a.action_key == rec.action_key), None)
    
    gap = db.query(Gap).filter(Gap.id == rec.gap_id).first()
    
    if not gap or not action_def:
        raise HTTPException(status_code=500, detail="Inconsistent state")
        
    effort_mult = 1.0 / (rec.effort ** 0.5)
    proj_mult = 1.10 if rec.project_id else 1.00
    evidence_pot = rec.priority_score / (gap.severity * effort_mult * proj_mult) if gap.severity > 0 else 0
    
    traceability = TraceabilityInfo(
        gap_severity=gap.severity,
        evidence_potential=evidence_pot,
        effort_multiplier=effort_mult,
        project_context_multiplier=proj_mult,
        expected_evidence_types=[t.value for t in action_def.expected_evidence_types],
        why_this_action=f"This addresses your {gap.severity} severity gap in {action_def.skill_name}.",
        why_this_project=f"This project lacks sufficient {action_def.expected_evidence_types[0].value if action_def.expected_evidence_types else 'evidence'}." if rec.project_id else None
    )
    
    return RecommendationResponse(
        id=rec.id,
        action_key=rec.action_key,
        title=rec.title,
        description=rec.description,
        target_skill=action_def.skill_name,
        current_state=gap.actual_state,
        required_state=gap.required_state,
        effort=rec.effort,
        priority_score=rec.priority_score,
        project_id=rec.project_id,
        traceability=traceability
    )

@router.post("/next-best-action/complete", dependencies=[Depends(verify_csrf_token)])
def complete_action(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.project_id:
        proj = db.query(Project).filter(Project.id == payload.project_id, Project.user_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found or ownership mismatch")

    history = ActionHistory(
        user_id=current_user.id,
        action_key=payload.action_key,
        project_id=payload.project_id,
        status=ActionHistoryStatus.COMPLETED,
        completed_at=datetime.now(timezone.utc)
    )
    db.add(history)
    db.commit()
    
    recalculate_next_best_action(current_user.id, db)
    return {
        "status": "success",
        "message": "Work marked complete. Sync your repository so NEXUS can verify the evidence."
    }

@router.post("/next-best-action/dismiss", dependencies=[Depends(verify_csrf_token)])
def dismiss_action(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.project_id:
        proj = db.query(Project).filter(Project.id == payload.project_id, Project.user_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found or ownership mismatch")

    history = ActionHistory(
        user_id=current_user.id,
        action_key=payload.action_key,
        project_id=payload.project_id,
        status=ActionHistoryStatus.DISMISSED
    )
    db.add(history)
    db.commit()
    
    recalculate_next_best_action(current_user.id, db)
    return {"status": "success"}

@router.post("/next-best-action/begin", dependencies=[Depends(verify_csrf_token)])
def begin_action(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.project_id:
        proj = db.query(Project).filter(Project.id == payload.project_id, Project.user_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found or ownership mismatch")

    history = ActionHistory(
        user_id=current_user.id,
        action_key=payload.action_key,
        project_id=payload.project_id,
        status=ActionHistoryStatus.STARTED
    )
    db.add(history)
    db.commit()
    
    return {
        "status": "success",
        "message": "Proof Quest initialized. Build the implementation in your repository, then sync."
    }

# ── 2. Proof Quest Engine API Endpoints ──────────────────────────────
@router.get("/quests", response_model=List[ProofQuestSummary])
def list_proof_quests(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns the primary Proof Quest and secondary eligible quests."""
    quests = get_available_quests(current_user.id, db)
    return quests

@router.get("/quests/{action_key}", response_model=ProofQuestDetail)
def get_proof_quest_detail(
    action_key: str,
    project_id: Optional[int] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Returns the comprehensive Proof Quest mission briefing."""
    if project_id:
        proj = db.query(Project).filter(Project.id == project_id, Project.user_id == current_user.id).first()
        if not proj:
            raise HTTPException(status_code=404, detail="Project not found or ownership mismatch")

    detail = get_quest_detail(current_user.id, action_key, db, project_id=project_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Proof Quest not found")
    return detail

@router.post("/quests/begin", dependencies=[Depends(verify_csrf_token)])
def begin_proof_quest(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return begin_action(payload, current_user, db)

@router.post("/quests/complete", dependencies=[Depends(verify_csrf_token)])
def complete_proof_quest(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return complete_action(payload, current_user, db)

@router.post("/quests/dismiss", dependencies=[Depends(verify_csrf_token)])
def dismiss_proof_quest(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return dismiss_action(payload, current_user, db)

@router.get("/quests/{action_key}/verification", response_model=QuestVerificationResponse)
def get_quest_verification(
    action_key: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Inspects latest repository evidence to evaluate whether this quest was verified."""
    return verify_quest_outcome(current_user.id, action_key, db)
