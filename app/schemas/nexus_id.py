from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Public Profile Schemas ---

class PublicProjectSummary(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    verified_signals: List[str] = []
    detected_technologies: List[str] = []
    proof_summary: str

class PublicProofItem(BaseModel):
    title: str
    signal_name: str
    observation_summary: str
    project_name: str
    type: str

class PublicJourneyMilestone(BaseModel):
    stage_number: int
    title: str
    detail: str
    date_str: str

class PublicEngineeringSignature(BaseModel):
    core_signals: List[str] = []
    technical_domains: List[str] = []

class PublicProfileResponse(BaseModel):
    nexus_id: str
    public_slug: str
    name: str
    target_role: Optional[str] = None
    bio: Optional[str] = None
    engineering_signature: PublicEngineeringSignature
    proven_signals: List[str] = []
    developing_signals: List[str] = []
    unexplored_signals: Optional[List[str]] = None
    featured_projects: List[PublicProjectSummary] = []
    verified_proof: List[PublicProofItem] = []
    journey_milestones: Optional[List[PublicJourneyMilestone]] = None
    external_links: Dict[str, str] = {}
    contact_email: Optional[str] = None
    last_surveyed: Optional[str] = None

class PublicAtlasLandmark(BaseModel):
    project_name: str
    signals: List[str] = []

class PublicAtlasTerritory(BaseModel):
    category: str
    landmarks: List[PublicAtlasLandmark] = []
    proven_count: int

class PublicAtlasResponse(BaseModel):
    nexus_id: str
    target_role: Optional[str] = None
    territories: List[PublicAtlasTerritory] = []

# --- Settings & Management Schemas ---

class ProfileHealthItem(BaseModel):
    key: str
    label: str
    is_completed: bool
    status_hint: str

class NexusIdSettingsResponse(BaseModel):
    nexus_id: str
    public_slug: str
    public_profile: bool
    bio: Optional[str] = None
    external_links: Dict[str, str] = {}
    show_journey: bool
    show_proof: bool
    show_unexplored: bool
    show_email: bool
    featured_project_ids: List[int] = []
    available_projects: List[Dict[str, Any]] = []
    public_url: str
    profile_health: List[ProfileHealthItem] = []

class NexusIdSettingsUpdate(BaseModel):
    public_profile: Optional[bool] = None
    public_slug: Optional[str] = None
    bio: Optional[str] = None
    external_links: Optional[Dict[str, str]] = None
    show_journey: Optional[bool] = None
    show_proof: Optional[bool] = None
    show_unexplored: Optional[bool] = None
    show_email: Optional[bool] = None
    featured_project_ids: Optional[List[int]] = None
    publish_project_ids: Optional[List[int]] = None  # IDs of projects to set is_public = True

# --- Career Layer: Claims vs Proof ---

class ClaimCreateRequest(BaseModel):
    claim_text: str = Field(..., min_length=1, max_length=100)
    category: Optional[str] = None

class ClaimEvaluationItem(BaseModel):
    id: int
    claim_text: str
    status: str  # SUPPORTED, PARTIALLY_SUPPORTED, NOT_YET_SUPPORTED
    supporting_evidence: List[str] = []
    guidance: str

class ClaimListResponse(BaseModel):
    claims: List[ClaimEvaluationItem] = []

# --- Career Layer: Portfolio Selector & Recruiter View ---

class PortfolioSelectorResponse(BaseModel):
    target_role: str
    recommended_project_id: Optional[int] = None
    recommended_project_name: Optional[str] = None
    reasoning: List[str] = []
    alternative_projects: List[Dict[str, Any]] = []

class RecruiterViewResponse(BaseModel):
    target_role: str
    immediately_visible: Dict[str, Any]
    still_unclear: List[str]

class CareerSnapshotResponse(BaseModel):
    target_role: str
    proven_signals: List[str] = []
    developing_signals: List[str] = []
    featured_project: Optional[str] = None
    recent_growth: Optional[str] = None
    next_area_to_strengthen: Optional[str] = None
