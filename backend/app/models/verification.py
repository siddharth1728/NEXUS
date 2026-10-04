"""Verification and Evidence Models."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.action import Action
    from app.models.execution import ExecutionRecord
    from app.models.tenant import Tenant


class EvidenceRequirement(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A deterministic requirement that must be proven to verify an Action."""

    __tablename__ = "evidence_requirements"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    action_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("actions.id", ondelete="CASCADE"), index=True
    )

    # What tool/connector to use for verification
    tool_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Parameters to pass to the tool
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Expected result assertions (e.g. {"state": "open"})
    expected_state: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    action: Mapped["Action"] = relationship("Action")
    evidence: Mapped[list["Evidence"]] = relationship(
        "Evidence", back_populates="requirement", cascade="all, delete-orphan"
    )


class Evidence(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Cryptographically or deterministically sourced proof satisfying a requirement."""

    __tablename__ = "evidence"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    requirement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("evidence_requirements.id", ondelete="CASCADE"), index=True
    )
    execution_record_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("executions.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # The actual payload from the external system
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Provenance metadata (e.g. request ID, timestamp from provider)
    provenance: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Did this evidence satisfy the requirement?
    is_valid: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    requirement: Mapped["EvidenceRequirement"] = relationship(
        "EvidenceRequirement", back_populates="evidence"
    )
    execution_record: Mapped["ExecutionRecord | None"] = relationship("ExecutionRecord")
