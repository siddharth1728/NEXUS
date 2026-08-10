from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.project import Evidence, RepositorySnapshot, Project, Artifact, RawObservation
from app.models.taxonomy import Skill

def get_evidence_by_snapshot(db: Session, snapshot_id: int, user_id: int):
    # Verify snapshot ownership
    snapshot = db.query(RepositorySnapshot).join(Project).filter(
        RepositorySnapshot.id == snapshot_id,
        Project.user_id == user_id
    ).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
        
    return db.query(Evidence).join(
        RawObservation
    ).join(
        Artifact
    ).filter(
        Artifact.snapshot_id == snapshot_id
    ).all()

def get_evidence(db: Session, evidence_id: int, user_id: int) -> Evidence:
    evidence = db.query(Evidence).join(
        RawObservation
    ).join(
        Artifact
    ).join(
        RepositorySnapshot
    ).join(
        Project
    ).filter(
        Evidence.id == evidence_id,
        Project.user_id == user_id
    ).first()
    
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    return evidence

def get_evidence_by_skill(db: Session, skill_id: int, user_id: int):
    # Ensure the user only sees their own evidence that maps to this skill
    # evidence -> evidence_skills -> ... -> project
    from app.models.project import EvidenceSkill
    
    return db.query(Evidence).join(
        RawObservation
    ).join(
        Artifact
    ).join(
        RepositorySnapshot
    ).join(
        Project
    ).join(
        EvidenceSkill, EvidenceSkill.evidence_id == Evidence.id
    ).filter(
        Project.user_id == user_id,
        EvidenceSkill.skill_id == skill_id
    ).all()
