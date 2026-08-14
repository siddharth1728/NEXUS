from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Dict
from datetime import datetime

class ProjectMetadataInfo(BaseModel):
    project_id: int
    name: str
    github_repo_id: int
    repo_url: Optional[str] = None
    default_branch: Optional[str] = None
    latest_commit_sha: Optional[str] = None
    last_surveyed: Optional[datetime] = None
    snapshot_status: str
    artifact_count: int
    observation_count: int
    detected_languages: List[str]
    detected_frameworks: List[str]

class ProjectEvidenceItem(BaseModel):
    id: int
    type: str
    quality_score: float
    freshness_weight: float
    source_reference: Optional[str] = None
    raw_observation_text: Optional[str] = None
    target_skills: List[str]

class ProjectEvidenceCategory(BaseModel):
    category_name: str
    evidence_count: int
    items: List[ProjectEvidenceItem]

class ProjectSignalItem(BaseModel):
    skill_name: str
    category: str
    state: str  # STRONG, DEVELOPING, WEAK, UNEXPLORED
    evidence_count: int
    quality_avg: float
    explanation: str

class ProjectDimensionCoverage(BaseModel):
    dimension_name: str  # CORE_API, DATABASE, AUTHENTICATION, TESTING, DEPLOYMENT, CI_CD
    display_name: str
    status: str          # PROVEN, DEVELOPING, UNEXPLORED, NOT_OBSERVED
    evidence_notes: str

class ProjectGrowthOpportunity(BaseModel):
    action_key: str
    title: str
    skill_name: str
    mission_brief: str
    why_this_project: str
    verification_expectations: str
    status: str

class ProjectEvolutionStep(BaseModel):
    survey_number: int
    snapshot_id: int
    captured_at: datetime
    commit_sha: Optional[str] = None
    status: str
    artifact_count: int
    observation_count: int
    new_evidence_types: List[str]
    summary: str

class ProjectGuidance(BaseModel):
    recommendation: str  # IMPROVE_THIS_PROJECT, EXPAND_REPERTOIRE, SURVEY_REQUIRED
    headline: str
    rationale: str
    strong_dimensions: List[str]
    missing_dimensions: List[str]

class ProjectIntelligenceResponse(BaseModel):
    metadata: ProjectMetadataInfo
    depth_level: str     # FOUNDATION, BUILDING, EXPANDING, BROAD_SIGNAL, UNSURVEYED
    signals: List[ProjectSignalItem]
    evidence_categories: List[ProjectEvidenceCategory]
    dimensions: List[ProjectDimensionCoverage]
    growth_opportunities: List[ProjectGrowthOpportunity]
    guidance: ProjectGuidance
    evolution: List[ProjectEvolutionStep]
