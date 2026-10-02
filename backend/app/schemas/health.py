"""NEXUS Health and Readiness Schemas."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class HealthStatus(StrEnum):
    """Health status indicator."""

    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    DEGRADED = "DEGRADED"


class ComponentHealth(BaseModel):
    """Health details for an individual subsystem component."""

    status: HealthStatus
    latency_ms: float | None = None
    message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)


class HealthResponse(BaseModel):
    """Liveness check response."""

    status: HealthStatus = HealthStatus.HEALTHY
    app_name: str
    app_version: str
    environment: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ReadinessResponse(BaseModel):
    """Readiness check response verifying all critical dependencies."""

    status: HealthStatus
    app_name: str
    app_version: str
    components: dict[str, ComponentHealth]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
