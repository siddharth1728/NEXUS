from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict
from datetime import datetime

class TraceabilityInfo(BaseModel):
    gap_severity: float
    evidence_potential: float
    effort_multiplier: float
    project_context_multiplier: float
    expected_evidence_types: List[str]
    why_this_action: str
    why_this_project: Optional[str] = None

class RecommendationResponse(BaseModel):
    id: int
    action_key: str
    title: str
    description: str
    target_skill: str
    current_state: str
    required_state: str
    effort: int
    priority_score: float
    project_id: Optional[int] = None
    traceability: TraceabilityInfo

class ActionPayload(BaseModel):
    action_key: str
    project_id: Optional[int] = None

# ── Proof Quest Specific Schemas ─────────────────────────────────────
class ProofQuestSummary(BaseModel):
    action_key: str
    title: str
    description: str
    skill_name: str
    current_state: str
    target_state: str
    effort: int
    priority_score: float
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    is_primary: bool = False
    status: str = "AVAILABLE" # AVAILABLE, STARTED, COMPLETED, DISMISSED

class ProofQuestDetail(BaseModel):
    action_key: str
    title: str
    description: str
    mission_brief: str
    skill_name: str
    current_state: str
    target_state: str
    effort: int
    priority_score: float
    expected_evidence_types: List[str]
    expected_artifact_types: List[str]
    verification_expectations: str
    project_id: Optional[int] = None
    project_name: Optional[str] = None
    why_this_project: Optional[str] = None
    why_this_quest: str
    status: str = "AVAILABLE"

class QuestVerificationResponse(BaseModel):
    action_key: str
    skill_name: str
    verified: bool
    current_state: str
    previous_state: Optional[str] = None
    new_evidence_count: int
    what_nexus_found: List[str]
    what_is_missing: List[str]
    explanation: str
    next_recommended_action_key: Optional[str] = None
