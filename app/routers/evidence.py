from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.services import evidence_service

router = APIRouter()

@router.get("/evidence/{evidence_id}", tags=["Evidence"])
def get_evidence(evidence_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evidence = evidence_service.get_evidence(db, evidence_id, current_user.id)
    skills = [{"id": s.skill.id, "name": s.skill.name} for s in evidence.skills]
    
    return {
        "id": evidence.id,
        "type": evidence.type,
        "quality_score": evidence.quality_score,
        "freshness_weight": evidence.freshness_weight,
        "source_reference": evidence.source_reference,
        "skills": skills
    }

@router.get("/evidence/{evidence_id}/skills", tags=["Evidence"])
def get_evidence_skills(evidence_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    evidence = evidence_service.get_evidence(db, evidence_id, current_user.id)
    skills = [{"id": s.skill.id, "name": s.skill.name, "category": s.skill.category} for s in evidence.skills]
    return skills
