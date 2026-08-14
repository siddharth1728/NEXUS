from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class EvidenceDetail(BaseModel):
    evidence_id: int
    type: str
    artifact_path: str
    observation: str

class SignalNode(BaseModel):
    skill_id: int
    skill_name: str
    state: str
    evidence: List[EvidenceDetail]

class UnexploredNode(BaseModel):
    skill_id: int
    skill_name: str
    category: str

class LandmarkNode(BaseModel):
    project_id: int
    project_name: str
    signals: List[SignalNode]

class AtlasTerritory(BaseModel):
    category: str
    landmarks: List[LandmarkNode]
    unexplored: List[UnexploredNode]

class MeaningfulTransition(BaseModel):
    skill_name: str
    previous_state: Optional[str]
    new_state: str
    changed_at: datetime

class Discovery(BaseModel):
    type: str
    artifact_path: str
    observation: str

class EngineeringJourney(BaseModel):
    meaningful_transitions: List[MeaningfulTransition]
    recent_discoveries: List[Discovery]

class EngineeringIdentity(BaseModel):
    target_role: Optional[str]
    github_username: Optional[str] = None
    last_synced: Optional[datetime] = None
    atlas_territories: List[AtlasTerritory]
    engineering_journey: EngineeringJourney
