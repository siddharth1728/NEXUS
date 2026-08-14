from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class CopilotAskRequest(BaseModel):
    query: str = Field(..., max_length=2000, description="Natural language question")
    project_id: Optional[int] = None
    concept_key: Optional[str] = None
    skill_name: Optional[str] = None

class CopilotAskResponse(BaseModel):
    query: str
    response: str
    verified_context_used: bool
    context_summary: Optional[str] = None
    related_lab_concept: Optional[str] = None
    related_proof_quest: Optional[str] = None

class InterviewStartRequest(BaseModel):
    project_id: int
    difficulty: str = Field(default="INTERMEDIATE", description="FOUNDATION, INTERMEDIATE, or ADVANCED")

class InterviewStartResponse(BaseModel):
    session_id: str
    project_id: int
    project_name: str
    target_role: str
    difficulty: str
    first_question: str
    question_index: int
    total_questions: int
    verified_signals: List[str]
    verified_technologies: List[str]
    context_indicator: Dict[str, Any]

class InterviewAnswerRequest(BaseModel):
    session_id: str
    answer: str = Field(..., max_length=2000, description="Student's answer to the technical question")

class InterviewFeedback(BaseModel):
    status: str  # STRONG_EXPLANATION, PARTIAL_EXPLANATION, NEEDS_CLARIFICATION
    what_you_got_right: str
    what_you_missed: str
    better_explanation: str
    follow_up_question: Optional[str] = None

class InterviewAnswerResponse(BaseModel):
    session_id: str
    question_index: int
    total_questions: int
    feedback: InterviewFeedback
    next_question: Optional[str] = None
    is_finished: bool
    summary: Optional[Dict[str, Any]] = None

class InterviewSummaryResponse(BaseModel):
    session_id: str
    project_name: str
    target_role: str
    difficulty: str
    topics_discussed: List[str]
    strong_explanations: List[str]
    topics_to_strengthen: List[str]
    suggested_lab_concepts: List[str]
    suggested_proof_quests: List[str]
    truth_contract_notice: str = "This is AI engineering coaching feedback. It has NOT modified your authoritative NEXUS Skill State or Gaps."
