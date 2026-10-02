"""Schemas for retrieval and context assembly."""
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RetrievalResult(BaseModel):
    """A single retrieved chunk of context."""

    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content: str
    source_location: dict[str, Any]

    retrieval_method: Literal["VECTOR", "KEYWORD", "HYBRID"]
    retrieval_score: float

    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True, from_attributes=True)


class RetrievalQuery(BaseModel):
    """Parameters for executing a retrieval operation."""

    query: str
    tenant_id: uuid.UUID
    document_ids: list[uuid.UUID] | None = None

    top_k: int = 5
    min_score: float = 0.0

    # Can configure vector vs keyword vs hybrid weights
    method: Literal["VECTOR", "KEYWORD", "HYBRID"] = "HYBRID"
    alpha: float = 0.5  # 1.0 = pure vector, 0.0 = pure keyword
