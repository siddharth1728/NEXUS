from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class TraceabilityInfo(BaseModel):
    gap_severity: float
    evidence_potential: float
    effort_multiplier: float
    project_context_multiplier: float
    expected_evidence_types: List[str]
    why_this_action: str
    why_this_project: Optional[str]

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
