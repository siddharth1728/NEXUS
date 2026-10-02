"""Execution Models for Tracking Action Execution."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ApprovalDecision, Capability, ExecutionState, PolicyDecision

if TYPE_CHECKING:
    from app.models.action import Action
    from app.models.tenant import Tenant
    from app.models.user import User


class ExecutionRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persistent history of execution requests and results."""

    __tablename__ = "executions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )

    action_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("actions.id", ondelete="CASCADE"), index=True
    )

    requester_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    agent_id: Mapped[str] = mapped_column(String(128), nullable=False)
    capability: Mapped[Capability] = mapped_column(String(64), nullable=False, index=True)
    tool_id: Mapped[str] = mapped_column(String(128), nullable=False)

    # Execution Metadata
    parameters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    state: Mapped[ExecutionState] = mapped_column(String(32), default=ExecutionState.PENDING, nullable=False, index=True)

    # Policy and Approval
    policy_decision: Mapped[PolicyDecision | None] = mapped_column(String(32), nullable=True)
    approval_decision: Mapped[ApprovalDecision | None] = mapped_column(String(32), nullable=True)
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approval_reason: Mapped[str | None] = mapped_column(String, nullable=True)

    # Result
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    action: Mapped["Action"] = relationship("Action")
    requester: Mapped["User"] = relationship("User", foreign_keys=[requester_id])
    approver: Mapped["User"] = relationship("User", foreign_keys=[approver_id])
