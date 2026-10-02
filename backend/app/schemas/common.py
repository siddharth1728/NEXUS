"""NEXUS Common API Schemas & Envelopes.

Defines standardized response envelopes, pagination contracts, and error structures.
"""

from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Structured error payload description."""

    code: str = Field(description="Machine-readable error code")
    message: str = Field(description="Human-readable error description")
    details: dict[str, Any] | list[Any] = Field(
        default_factory=dict,
        description="Contextual details or validation breakdown",
    )
    request_id: str | None = Field(default=None, description="Correlated request ID")

    model_config = ConfigDict(from_attributes=True)


class ErrorEnvelope(BaseModel):
    """Standardized top-level error response envelope."""

    error: ErrorDetail

    model_config = ConfigDict(from_attributes=True)


class APIResponse(BaseModel, Generic[T]):
    """Standardized top-level successful API response envelope."""

    data: T
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    request_id: str | None = None

    model_config = ConfigDict(from_attributes=True)


class PaginationParams(BaseModel):
    """Standardized query parameters for paginated endpoints."""

    page: int = Field(default=1, ge=1, description="1-indexed page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated list response."""

    items: list[T]
    total_count: int = Field(ge=0, description="Total number of items matching filter")
    page: int = Field(ge=1, description="Current page")
    page_size: int = Field(ge=1, description="Page size limit")
    total_pages: int = Field(ge=0, description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: list[T],
        total_count: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[T]":
        total_pages = (
            (total_count + params.page_size - 1) // params.page_size if total_count > 0 else 0
        )
        return cls(
            items=items,
            total_count=total_count,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )
