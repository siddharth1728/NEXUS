from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

VALID_PERMISSIONS = ["PROFILE", "PROJECTS", "PROOF", "JOURNEY", "ATLAS", "QUESTS", "LAB", "CLAIMS"]

# --- Mentor Schemas ---

class MentorInviteRequest(BaseModel):
    mentor_email: Optional[str] = None
    permissions: List[str] = Field(default=["PROFILE", "PROJECTS", "PROOF", "JOURNEY", "QUESTS"])
    expires_in_days: Optional[int] = Field(default=30, ge=1, le=365)

class MentorInviteResponse(BaseModel):
    relationship_id: int
    invite_token: str
    invite_url: str
    permissions: List[str]
    expires_at: Optional[str] = None

class MentorAcceptRequest(BaseModel):
    invite_token: str

class MentorNoteCreateRequest(BaseModel):
    note_text: str = Field(..., min_length=1, max_length=2000)
    recommended_quest_id: Optional[int] = None
    recommended_concept_key: Optional[str] = None

class MentorNoteResponse(BaseModel):
    id: int
    author_email: str
    note_text: str
    recommended_quest_id: Optional[int] = None
    recommended_concept_key: Optional[str] = None
    created_at: str

class MentoredStudentSummary(BaseModel):
    student_id: int
    student_name: str
    target_role: Optional[str] = None
    permissions: List[str] = []
    relationship_id: int
    since: str

class MentoredStudentDossier(BaseModel):
    student_id: int
    student_name: str
    nexus_id: str
    target_role: str
    granted_permissions: List[str]
    proven_signals: Optional[List[str]] = None
    developing_signals: Optional[List[str]] = None
    unexplored_signals: Optional[List[str]] = None
    featured_projects: Optional[List[Dict[str, Any]]] = None
    verified_proof: Optional[List[Dict[str, Any]]] = None
    journey_milestones: Optional[List[Dict[str, Any]]] = None
    active_quests: Optional[List[Dict[str, Any]]] = None
    mentor_notes: List[MentorNoteResponse] = []

# --- Reviewer & Project Review Links ---

class ReviewLinkCreateRequest(BaseModel):
    project_id: int
    label: Optional[str] = None
    expires_in_days: Optional[int] = Field(default=30, ge=1, le=365)

class ReviewLinkResponse(BaseModel):
    id: int
    project_id: int
    project_name: str
    token: str
    review_url: str
    expires_at: Optional[str] = None
    is_active: bool
    created_at: str

class ReviewProjectViewResponse(BaseModel):
    project_name: str
    student_nexus_id: str
    target_role: str
    detected_technologies: List[str] = []
    verified_signals: List[str] = []
    proof_ledger: List[Dict[str, Any]] = []
    questions_to_explore: List[str] = []
    atlas_context: Dict[str, Any] = {}

# --- Educator Observatory Schemas ---

class CohortCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    course_code: str = Field(..., min_length=2, max_length=50)

class CohortJoinRequest(BaseModel):
    invite_code: str

class CohortSummary(BaseModel):
    id: int
    name: str
    course_code: str
    invite_code: str
    member_count: int
    created_at: str

class EducatorObservatoryResponse(BaseModel):
    cohort_id: int
    name: str
    course_code: str
    student_count: int
    privacy_status: str  # "UNAVAILABLE_INSUFFICIENT_SIZE", "LIMITED_SUMMARY", "FULL_OBSERVATORY"
    privacy_note: str
    most_common_gap: Optional[str] = None
    most_common_signals: List[Dict[str, Any]] = []
    dominant_project_patterns: List[Dict[str, Any]] = []
    curriculum_recommendations: List[str] = []

# --- Team Schemas ---

class TeamCreateRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None

class TeamJoinRequest(BaseModel):
    invite_code: str

class TeamShareProjectRequest(BaseModel):
    project_id: int

class TeamCollaborationResponse(BaseModel):
    team_id: int
    team_name: str
    description: Optional[str] = None
    creator_id: int
    invite_code: str
    members_count: int
    members: List[Dict[str, Any]] = []
    shared_projects: List[Dict[str, Any]] = []
    collaboration_signals: List[Dict[str, Any]] = []

# --- Sharing Center Control Plane ---

class PermissionLedgerItem(BaseModel):
    id: str  # e.g., "mentor_12" or "team_4" or "review_7"
    entity_type: str  # "MENTOR", "COHORT", "TEAM", "REVIEW_LINK"
    name: str
    access_granted: List[str]
    granted_since: str
    expires_at: Optional[str] = None
    can_revoke: bool = True

class SharingCenterOverviewResponse(BaseModel):
    public_profile_enabled: bool
    public_slug: Optional[str] = None
    active_mentors_count: int
    active_cohorts_count: int
    active_teams_count: int
    active_review_links_count: int
    permissions_ledger: List[PermissionLedgerItem] = []
    recent_audit_events: List[Dict[str, Any]] = []
