from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User, UserSkill
from app.services import evidence_service
from app.models.taxonomy import Skill

router = APIRouter()

@router.get("/skills", tags=["Skills"])
def get_user_skills(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == current_user.id).all()
    return [
        {
            "skill_id": us.skill_id,
            "skill_name": us.skill.name,
            "state": us.state.value,
            "calculated_at": us.calculated_at,
            "calculation_version": us.calculation_version
        } for us in user_skills
    ]

@router.get("/skills/{skill_id}", tags=["Skills"])
def get_user_skill(skill_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_skill = db.query(UserSkill).filter(UserSkill.user_id == current_user.id, UserSkill.skill_id == skill_id).first()
    if not user_skill:
        raise HTTPException(status_code=404, detail="Skill state not found")
        
    return {
        "skill_id": user_skill.skill_id,
        "skill_name": user_skill.skill.name,
        "state": user_skill.state.value,
        "calculated_at": user_skill.calculated_at,
        "calculation_version": user_skill.calculation_version
    }

@router.get("/skills/{skill_id}/evidence", tags=["Evidence"])
def get_skill_evidence(skill_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
        
    evidence_list = evidence_service.get_evidence_by_skill(db, skill_id, current_user.id)
    return [
        {
            "id": e.id,
            "type": e.type,
            "quality_score": e.quality_score,
            "freshness_weight": e.freshness_weight,
            "source_reference": e.source_reference,
            "raw_observation_text": e.raw_observation.observation_text
        } for e in evidence_list
    ]
