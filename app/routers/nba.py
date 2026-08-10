from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.models.user import User, Gap
from app.models.action import Recommendation, ActionHistory, ActionHistoryStatus
from app.schemas.action import RecommendationResponse, TraceabilityInfo, ActionPayload
from app.dependencies.auth import get_current_user
from app.services.nba_engine import recalculate_next_best_action
from app.config.action_catalog import get_action_catalog

router = APIRouter()

@router.get("/next-best-action", response_model=RecommendationResponse)
def get_next_best_action(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rec = db.query(Recommendation).filter(Recommendation.user_id == current_user.id).first()
    
    if not rec:
        # Try to calculate if missing
        rec = recalculate_next_best_action(current_user.id, db)
        if not rec:
            raise HTTPException(status_code=404, detail="NO_ACTION")
            
    # Reconstruct traceability
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
        traceability=traceability
    )

@router.post("/next-best-action/complete")
def complete_action(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    history = ActionHistory(
        user_id=current_user.id,
        action_key=payload.action_key,
        project_id=payload.project_id,
        status=ActionHistoryStatus.COMPLETED
    )
    db.add(history)
    db.commit()
    
    recalculate_next_best_action(current_user.id, db)
    return {"status": "success"}

@router.post("/next-best-action/dismiss")
def dismiss_action(payload: ActionPayload, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
