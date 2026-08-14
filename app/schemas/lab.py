from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class ChallengeOptionSchema(BaseModel):
    text: str
    is_correct: bool
    explanation: str

class TryItChallengeSchema(BaseModel):
    prompt: str
    options: List[ChallengeOptionSchema]
    engineering_principle: str

class DiagramStepSchema(BaseModel):
    step_number: int
    label: str
    technical_detail: str
    layer: str

class ProjectEvidenceReferenceSchema(BaseModel):
    project_id: int
    project_name: str
    evidence_count: int
    sample_observations: List[str]
    sample_source_files: List[str]

class ConceptSummarySchema(BaseModel):
    concept_key: str
    title: str
    short_description: str
    domain: str
    difficulty: str
    related_skill_names: List[str]
    user_skill_state: Optional[str] = None
    observed_in_user_projects: List[str]
    is_gap_for_user: bool

class ConceptDetailSchema(BaseModel):
    concept_key: str
    title: str
    short_description: str
    domain: str
    difficulty: str
    related_skill_names: List[str]
    related_evidence_types: List[str]
    prerequisites: List[str]
    learning_objectives: List[str]
    why_it_matters: str
    how_it_appears_in_projects: str
    diagram_steps: List[DiagramStepSchema]
    try_it_challenge: TryItChallengeSchema
    explain_it_prompt: str
    related_action_key: Optional[str] = None
    user_projects_using_this: List[ProjectEvidenceReferenceSchema]
    why_user_is_seeing_this: str

class LabDiscoveryFeedResponse(BaseModel):
    featured_discovery: ConceptDetailSchema
    discovery_reason: str
    all_concepts: List[ConceptSummarySchema]
