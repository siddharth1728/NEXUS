from sqlalchemy.orm import Session
from sqlalchemy import exc
from fastapi import HTTPException
from datetime import datetime, timezone
import logging
from app.models.project import Project, RepositorySnapshot, Artifact, RawObservation, SnapshotStatus
from app.schemas.project import ProjectCreate
from app.services import github_service, artifact_service, observation_service

logger = logging.getLogger(__name__)

def create_project(db: Session, user_id: int, project_data: ProjectCreate) -> Project:
    project = Project(
        user_id=user_id,
        github_repo_id=project_data.github_repo_id,
        name=project_data.name
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get_project(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

def get_projects(db: Session, user_id: int):
    return db.query(Project).filter(Project.user_id == user_id).all()

async def sync_project(db: Session, project_id: int, user_id: int, github_username: str) -> RepositorySnapshot:
    project = get_project(db, project_id, user_id)
    
    # Check for PENDING or ANALYZING snapshots
    active_snapshot = db.query(RepositorySnapshot).filter(
        RepositorySnapshot.project_id == project.id,
        RepositorySnapshot.status.in_([SnapshotStatus.PENDING, SnapshotStatus.ANALYZING])
    ).first()
    
    if active_snapshot:
        raise HTTPException(status_code=409, detail="A synchronization is already in progress.")
        
    snapshot = RepositorySnapshot(
        project_id=project.id,
        status=SnapshotStatus.PENDING
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    
    try:
        # Resolve branch and HEAD SHA
        snapshot.status = SnapshotStatus.ANALYZING
        snapshot.analysis_started_at = datetime.now(timezone.utc)
        db.commit()
        
        meta = await github_service.get_repository_metadata(github_username, project.name)
        default_branch = meta["default_branch"]
        sha = await github_service.get_repository_branch_head(github_username, project.name, default_branch)
        
        snapshot.branch = default_branch
        snapshot.commit_sha = sha
        db.commit()
        
        # Discover tree
        tree_data = await github_service.get_repository_tree(github_username, project.name, sha)
        tree = tree_data.get("tree", [])
        
        artifacts_metadata = artifact_service.discover_artifacts(tree)
        
        for art_meta in artifacts_metadata:
            # File size limit
            if art_meta["size"] > 500 * 1024:
                # Keep artifact metadata but do not download
                artifact = Artifact(snapshot_id=snapshot.id, file_path=art_meta["file_path"], type=art_meta["type"])
                db.add(artifact)
                db.commit()
                db.refresh(artifact)
                
                obs = RawObservation(
                    artifact_id=artifact.id,
                    observation_text="Analysis skipped: file exceeds 500 KB limit",
                    line_numbers=None
                )
                db.add(obs)
                db.commit()
                continue
                
            # Valid file size
            content = await github_service.get_file_content(github_username, project.name, sha, art_meta["file_path"])
            if content:
                observations = observation_service.generate_observations(art_meta["type"], art_meta["file_path"], content)
                
                if observations:
                    artifact = Artifact(snapshot_id=snapshot.id, file_path=art_meta["file_path"], type=art_meta["type"])
                    db.add(artifact)
                    db.commit()
                    db.refresh(artifact)
                    
                    for obs_data in observations:
                        obs = RawObservation(
                            artifact_id=artifact.id,
                            observation_text=obs_data["text"],
                            line_numbers=obs_data["line_numbers"]
                        )
                        db.add(obs)
                    db.commit()
                
                # Delete content from memory explicitly just in case
                del content
                
        snapshot.analysis_completed_at = datetime.now(timezone.utc)
        
        if tree_data.get("truncated"):
            snapshot.error_message = "Warning: Repository tree was truncated by GitHub API. Analysis may be incomplete."
            
        from app.services import evidence_engine, skill_state_engine
        evidence_engine.rebuild_snapshot_evidence(snapshot.id, db)
        skill_state_engine.recalculate_user_skills(project.user_id, db)
            
        snapshot.status = SnapshotStatus.COMPLETED
        db.commit()
        
    except github_service.GitHubRateLimitException as e:
        snapshot.status = SnapshotStatus.FAILED
        snapshot.error_message = str(e)
        db.commit()
    except Exception as e:
        logger.error(f"Sync failed for project {project.id}: {e}")
        snapshot.status = SnapshotStatus.FAILED
        snapshot.error_message = "An error occurred during synchronization."
        db.commit()
        
    db.refresh(snapshot)
    return snapshot

def get_snapshot(db: Session, snapshot_id: int, user_id: int) -> RepositorySnapshot:
    snapshot = db.query(RepositorySnapshot).join(Project).filter(
        RepositorySnapshot.id == snapshot_id,
        Project.user_id == user_id
    ).first()
    
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")
    return snapshot

def get_snapshots(db: Session, project_id: int, user_id: int):
    get_project(db, project_id, user_id)  # Validate ownership
    return db.query(RepositorySnapshot).filter(RepositorySnapshot.project_id == project_id).order_by(RepositorySnapshot.captured_at.desc()).all()

def get_artifacts(db: Session, snapshot_id: int, user_id: int):
    get_snapshot(db, snapshot_id, user_id)
    return db.query(Artifact).filter(Artifact.snapshot_id == snapshot_id).all()

def get_observations(db: Session, snapshot_id: int, user_id: int):
    get_snapshot(db, snapshot_id, user_id)
    return db.query(RawObservation).join(Artifact).filter(Artifact.snapshot_id == snapshot_id).all()
