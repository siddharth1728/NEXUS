"""Verification API Schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRequirementBase(BaseModel):
    """Shared properties for Evidence Requirements."""

    action_id: uuid.UUID
    tool_id: str = Field(..., max_length=128)
    parameters: dict[str, Any] = Field(default_factory=dict)
    expected_state: dict[str, Any] = Field(default_factory=dict)


class EvidenceRequirementCreate(EvidenceRequirementBase):
    """Properties to receive on creation."""
    pass


class EvidenceRequirementResponse(EvidenceRequirementBase):
    """Properties to return for Evidence Requirement."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceBase(BaseModel):
    """Shared properties for Evidence."""

    requirement_id: uuid.UUID
    execution_record_id: uuid.UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    is_valid: bool = False


class EvidenceCreate(EvidenceBase):
    """Properties to receive on creation."""
    pass


class EvidenceResponse(EvidenceBase):
    """Properties to return for Evidence."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationResult(BaseModel):
    """The result of evaluating evidence against a requirement."""

    requirement_id: uuid.UUID
    is_verified: bool
    reason: str
    evidence_id: uuid.UUID | None = None
