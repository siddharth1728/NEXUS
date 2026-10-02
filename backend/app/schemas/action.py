"""Action API Schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ActionStatus, ConfidenceLevel, EdgeRelationType


class ActionBase(BaseModel):
    """Shared properties for Actions."""

    title: str = Field(..., max_length=512)
    description: str
    priority: str = Field(default="P2", max_length=16)
    due_date: datetime | None = None
    is_hard_deadline: bool = False
    assignee_id: uuid.UUID | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.HIGH


class ActionCreate(ActionBase):
    """Properties to receive on Action creation."""

    source_document_id: uuid.UUID | None = None


class ActionUpdate(BaseModel):
    """Properties to receive on Action update."""

    title: str | None = Field(None, max_length=512)
    description: str | None = None
    priority: str | None = Field(None, max_length=16)
    due_date: datetime | None = None
    is_hard_deadline: bool | None = None
    assignee_id: uuid.UUID | None = None


class ActionStateTransition(BaseModel):
    """Properties for transitioning an Action's state."""

    new_status: ActionStatus


class ActionResponse(ActionBase):
    """Properties to return for an Action."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    status: ActionStatus
    source_document_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionEdgeCreate(BaseModel):
    """Properties to create a dependency edge."""

    target_id: uuid.UUID
    relation_type: EdgeRelationType
    metadata_payload: dict[str, Any] = Field(default_factory=dict)


class ActionEdgeResponse(BaseModel):
    """Properties to return for an Action Edge."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    source_id: uuid.UUID
    target_id: uuid.UUID
    relation_type: EdgeRelationType
    metadata_payload: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
