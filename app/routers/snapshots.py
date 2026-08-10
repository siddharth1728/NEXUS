from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.project import RepositorySnapshotResponse, ArtifactResponse, RawObservationResponse
from app.services import project_service

router = APIRouter(prefix="/snapshots", tags=["snapshots"])

@router.get("/{snapshot_id}", response_model=RepositorySnapshotResponse)
def get_snapshot(snapshot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    s = project_service.get_snapshot(db, snapshot_id, current_user.id)
    return RepositorySnapshotResponse(
        id=s.id,
        project_id=s.project_id,
        commit_sha=s.commit_sha,
        branch=s.branch,
        captured_at=s.captured_at,
        analysis_started_at=s.analysis_started_at,
        analysis_completed_at=s.analysis_completed_at,
        status=s.status,
        error_message=s.error_message,
        artifact_count=len(s.artifacts),
        observation_count=sum(len(a.observations) for a in s.artifacts)
    )

@router.get("/{snapshot_id}/artifacts", response_model=List[ArtifactResponse])
def get_artifacts(snapshot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    artifacts = project_service.get_artifacts(db, snapshot_id, current_user.id)
    return [ArtifactResponse(id=a.id, snapshot_id=a.snapshot_id, file_path=a.file_path, type=a.type) for a in artifacts]

@router.get("/{snapshot_id}/observations", response_model=List[RawObservationResponse])
def get_observations(snapshot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    observations = project_service.get_observations(db, snapshot_id, current_user.id)
    return [RawObservationResponse(id=o.id, artifact_id=o.artifact_id, observation_text=o.observation_text, line_numbers=o.line_numbers) for o in observations]

@router.get("/{snapshot_id}/evidence", tags=["Evidence"])
def get_snapshot_evidence(snapshot_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.services import evidence_service
    evidence_list = evidence_service.get_evidence_by_snapshot(db, snapshot_id, current_user.id)
    return [
        {
            "id": e.id,
            "type": e.type,
            "quality_score": e.quality_score,
            "freshness_weight": e.freshness_weight,
            "source_reference": e.source_reference,
            "skills": [{"id": s.skill.id, "name": s.skill.name} for s in e.skills]
        } for e in evidence_list
    ]
