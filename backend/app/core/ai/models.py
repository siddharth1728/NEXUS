"""NEXUS AI Request/Response Data Models."""

from typing import Any

from pydantic import BaseModel, Field


class AIRequest(BaseModel):
    """Normalized request for the AI Gateway."""

    provider: str
    model: str
    prompt: str
    system_instruction: str | None = None
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    require_structured_output: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str | None = None


class AIResponse(BaseModel):
    """Normalized response from the AI Gateway."""

    content: str
    provider: str
    model: str
    provider_request_id: str | None = None
    usage_metadata: dict[str, Any] | None = None
    latency_ms: int | None = None
    is_structured: bool = False
