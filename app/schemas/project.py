from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime
from app.models.project import SnapshotStatus

class GitHubRepository(BaseModel):
    id: int
    name: str
    full_name: str
    description: Optional[str] = None
    default_branch: str
    html_url: str

class ProjectCreate(BaseModel):
    github_repo_id: int
    name: str

class ProjectResponse(BaseModel):
    id: int
    user_id: int
    github_repo_id: int
    name: str

class RawObservationResponse(BaseModel):
    id: int
    artifact_id: int
    observation_text: str
    line_numbers: Optional[str] = None

class ArtifactResponse(BaseModel):
    id: int
    snapshot_id: int
    file_path: str
    type: str

class RepositorySnapshotResponse(BaseModel):
    id: int
    project_id: int
    commit_sha: Optional[str] = None
    branch: Optional[str] = None
    captured_at: datetime
    analysis_started_at: Optional[datetime] = None
    analysis_completed_at: Optional[datetime] = None
    status: SnapshotStatus
    error_message: Optional[str] = None
    artifact_count: int = 0
    observation_count: int = 0
