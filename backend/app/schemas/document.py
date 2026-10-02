"""Document and ExtractionJob API Schemas."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import ExtractionJobStatus


class DocumentBase(BaseModel):
    """Shared properties for Documents."""

    title: str = Field(..., max_length=512)
    source_type: str = Field(..., max_length=64)
    source_uri: str | None = None
    sha256_hash: str = Field(..., max_length=64)
    raw_metadata: dict[str, Any] = Field(default_factory=dict)


class DocumentCreate(DocumentBase):
    """Properties to receive on Document creation."""

    pass


class DocumentResponse(DocumentBase):
    """Properties to return for a Document."""

    id: uuid.UUID
    tenant_id: uuid.UUID
    owner_id: uuid.UUID | None
    processing_status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtractionJobCreate(BaseModel):
    """Properties to create an ExtractionJob."""

    document_id: uuid.UUID


class ExtractionJobStateTransition(BaseModel):
    """Properties for transitioning an ExtractionJob's state."""

    new_status: ExtractionJobStatus
    error_category: str | None = None


class ExtractionJobResponse(BaseModel):
    """Properties to return for an ExtractionJob."""

    id: uuid.UUID
    document_id: uuid.UUID
    status: ExtractionJobStatus
    started_at: datetime | None
    completed_at: datetime | None
    error_category: str | None
    retry_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    """Properties to return for a DocumentChunk."""

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    content: str
    structural_type: str
    source_location: dict[str, Any]
    chunk_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
