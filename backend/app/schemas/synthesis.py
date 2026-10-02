"""Action Synthesis Schemas for Phase 02A."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ConfidenceLevel


class ProvenanceReference(BaseModel):
    """Reference to a specific chunk and document supporting a candidate action."""
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    chunk_index: int | None = None
    source_location: dict[str, Any] = Field(default_factory=dict)


class SynthesisContext(BaseModel):
    """Bounded context provided to the Synthesis Engine."""
    tenant_id: uuid.UUID
    facts: list[dict[str, Any]] = Field(default_factory=list)
    entities: list[dict[str, Any]] = Field(default_factory=list)
    temporal_information: list[dict[str, Any]] = Field(default_factory=list)
    requirements: list[dict[str, Any]] = Field(default_factory=list)
    candidate_actions: list[dict[str, Any]] = Field(default_factory=list)
    rag_context: list[dict[str, Any]] = Field(default_factory=list)
    personalization: dict[str, Any] | None = None
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    dependencies: list[dict[str, Any]] = Field(default_factory=list)


class CandidateAction(BaseModel):
    """An AI proposal for an Action, prior to domain validation and persistence."""

    title: str = Field(..., description="Short, actionable title.")
    description: str = Field(..., description="Detailed description of what must be done.")
    classification: Literal["EXPLICIT", "INFERRED"] = Field(
        ..., description="Whether the action is explicitly stated or inferred from context."
    )
    confidence: ConfidenceLevel = Field(..., description="Strength of evidence supporting this action.")
    deadline: str | None = Field(None, description="Extracted deadline expression or resolved ISO date.")
    priority_signal: Literal["HIGH", "MEDIUM", "LOW"] | None = Field(None, description="Signal for priority based on urgency/importance.")
    actor_candidate: str | None = Field(None, description="Extracted hint about who should perform the action.")

    source_refs: list[ProvenanceReference] = Field(default_factory=list, description="Source references providing evidence.")
    supporting_quotes: list[str] = Field(default_factory=list, description="Verbatim quotes from sources.")
    dependency_refs: list[str] = Field(default_factory=list, description="String references to other candidate titles this depends on.")
    rationale: str = Field(..., description="Machine-readable rationale explaining why this action is required.")

    model_config = ConfigDict(from_attributes=True)


class CandidateActionValidationResult(BaseModel):
    """Result of validating a candidate action."""
    is_valid: bool
    status: Literal["APPROVED", "REJECTED", "REQUIRES_REVIEW"]
    reasons: list[str] = Field(default_factory=list)
    validated_action_data: dict[str, Any] | None = None


class SynthesisResult(BaseModel):
    """Output from the Synthesis Engine."""
    candidates: list[CandidateAction] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata about the synthesis run (model, prompt version, etc.)")
