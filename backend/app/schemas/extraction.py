"""Schemas for Grounded AI Information Extraction."""

import uuid
from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Provider / LLM output schemas
# ---------------------------------------------------------------------------


class FactOutput(BaseModel):
    """Fact extracted directly by the LLM."""

    statement: str = Field(description="Normalized statement of the fact.")
    verbatim_quote: str = Field(description="Exact quote from the chunk supporting this fact.")
    confidence: Literal["HIGH", "MEDIUM", "REQUIRES_REVIEW", "UNKNOWN", "CONFLICT"] = Field(
        description="Confidence that this fact is accurately supported by the source text."
    )
    is_inferred: bool = Field(
        description="True if the fact was inferred from context, False if explicitly stated."
    )


class EntityOutput(BaseModel):
    """Entity extracted directly by the LLM."""

    name: str = Field(description="Normalized name of the entity.")
    type: Literal[
        "PERSON",
        "ORGANIZATION",
        "DEPARTMENT",
        "COURSE",
        "PROJECT",
        "SYSTEM",
        "LOCATION",
        "DOCUMENT",
        "ROLE",
        "OTHER",
    ] = Field(description="The category of the entity.")
    verbatim_quote: str = Field(description="Exact quote of the entity as it appears in text.")


class TemporalOutput(BaseModel):
    """Temporal or deadline extraction."""

    temporal_expression: str = Field(
        description="The original temporal phrase (e.g. 'tomorrow', 'Oct 8 at 5 PM')."
    )
    verbatim_quote: str = Field(description="Exact quote containing the temporal expression.")
    reference_date_resolved: str | None = Field(
        default=None,
        description="ISO-8601 date string if resolving is possible with certainty, else null.",
    )
    is_deadline: bool = Field(
        default=False, description="True if this temporal expression acts as a deadline."
    )


class RequirementOutput(BaseModel):
    """Explicit requirement extracted by the LLM."""

    requirement: str = Field(description="The explicit requirement (e.g. 'Upload ID proof').")
    condition: str | None = Field(default=None, description="Conditions tied to the requirement.")
    verbatim_quote: str = Field(description="Exact quote from the chunk.")


class CandidateActionOutput(BaseModel):
    """Action-like statements that may become Nexus Tasks."""

    action_statement: str = Field(
        description="The extracted candidate action (e.g. 'Submit the registration form')."
    )
    assignee_hint: str | None = Field(
        default=None, description="Who is supposed to do this, if mentioned."
    )
    verbatim_quote: str = Field(description="Exact quote supporting this candidate action.")


class ChunkExtractionOutput(BaseModel):
    """The strict JSON schema the LLM is expected to return for a single chunk."""

    facts: list[FactOutput] = Field(default_factory=list)
    entities: list[EntityOutput] = Field(default_factory=list)
    temporal_items: list[TemporalOutput] = Field(default_factory=list)
    requirements: list[RequirementOutput] = Field(default_factory=list)
    candidate_actions: list[CandidateActionOutput] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Domain API response schemas (with provenance)
# ---------------------------------------------------------------------------


class ProvenanceSchema(BaseModel):
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    chunk_index: int
    source_location: dict[str, Any]


class ExtractedFactResponse(BaseModel):
    id: uuid.UUID
    statement: str
    verbatim_quote: str
    confidence: str
    metadata: dict[str, Any] = Field(alias="metadata_")
    provenance: ProvenanceSchema

    model_config = {"populate_by_name": True, "from_attributes": True}


class ExtractionResultResponse(BaseModel):
    """Overall API response returning persisted facts and other items as metadata."""

    document_id: uuid.UUID
    facts: list[ExtractedFactResponse] = Field(default_factory=list)
    # Entities, Temporal Items, Requirements, and Candidate Actions are kept in memory
    # or serialized differently depending on how they are routed to the Action Graph later.
    # For Phase 01F, we will expose the full JSON metadata of what was extracted.
    raw_extraction_metadata: dict[str, Any] = Field(default_factory=dict)
