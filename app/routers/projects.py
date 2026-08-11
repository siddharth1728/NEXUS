from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session
from app.dependencies.auth import get_current_user
from app.core.csrf import verify_csrf_token
from app.database.database import get_db
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse, RepositorySnapshotResponse
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[ProjectResponse])
def get_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    projects = project_service.get_projects(db, current_user.id)
    return [ProjectResponse(id=p.id, user_id=p.user_id, github_repo_id=p.github_repo_id, name=p.name) for p in projects]

@router.post("/", response_model=ProjectResponse, dependencies=[Depends(verify_csrf_token)])
def create_project(project_data: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = project_service.create_project(db, current_user.id, project_data)
    return ProjectResponse(id=p.id, user_id=p.user_id, github_repo_id=p.github_repo_id, name=p.name)

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = project_service.get_project(db, project_id, current_user.id)
    return ProjectResponse(id=p.id, user_id=p.user_id, github_repo_id=p.github_repo_id, name=p.name)

@router.post("/{project_id}/sync", response_model=RepositorySnapshotResponse, dependencies=[Depends(verify_csrf_token)])
async def sync_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.profile or not current_user.profile.github_username:
        raise HTTPException(status_code=400, detail="GitHub username not set in profile")
    
    s = await project_service.sync_project(db, project_id, current_user.id, current_user.profile.github_username)
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

@router.get("/{project_id}/snapshots", response_model=List[RepositorySnapshotResponse])
def get_snapshots(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    snapshots = project_service.get_snapshots(db, project_id, current_user.id)
    result = []
    for s in snapshots:
        result.append(RepositorySnapshotResponse(
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
        ))
    return result
