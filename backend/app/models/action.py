"""Action and ActionEdge Models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ActionStatus, ConfidenceLevel, EdgeRelationType

if TYPE_CHECKING:
    from app.models.document import Document
    from app.models.tenant import Tenant
    from app.models.user import User


class Action(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """The central actionable entity in NEXUS."""

    __tablename__ = "actions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)

    # Domain state
    status: Mapped[ActionStatus] = mapped_column(
        String(32), default=ActionStatus.CANDIDATE, nullable=False, index=True
    )
    priority: Mapped[str] = mapped_column(String(16), default="P2", nullable=False)
    due_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    is_hard_deadline: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # AI-derived metadata / Evidence
    confidence: Mapped[ConfidenceLevel] = mapped_column(
        String(32), default=ConfidenceLevel.HIGH, nullable=False
    )
    source_document_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"), index=True, nullable=True
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="actions")
    assignee: Mapped["User | None"] = relationship("User", back_populates="actions")
    source_document: Mapped["Document | None"] = relationship("Document", back_populates="actions")

    # Edges where this action is the source (e.g., this action depends on the target)
    outgoing_edges: Mapped[list["ActionEdge"]] = relationship(
        "ActionEdge",
        foreign_keys="[ActionEdge.source_id]",
        back_populates="source",
        cascade="all, delete-orphan",
    )

    # Edges where this action is the target (e.g., this action is depended upon by the source)
    incoming_edges: Mapped[list["ActionEdge"]] = relationship(
        "ActionEdge",
        foreign_keys="[ActionEdge.target_id]",
        back_populates="target",
        cascade="all, delete-orphan",
    )


class ActionEdge(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Relational representation of Action Graph relationships."""

    __tablename__ = "action_edges"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )

    # Strictly typing this to Actions for Phase 01B foreign key integrity
    source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("actions.id", ondelete="CASCADE"), index=True, nullable=False
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("actions.id", ondelete="CASCADE"), index=True, nullable=False
    )

    relation_type: Mapped[EdgeRelationType] = mapped_column(String(32), nullable=False, index=True)

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "relation_type", name="uq_action_edge"),
    )

    # Relationships
    source: Mapped["Action"] = relationship(
        "Action", foreign_keys=[source_id], back_populates="outgoing_edges"
    )
    target: Mapped["Action"] = relationship(
        "Action", foreign_keys=[target_id], back_populates="incoming_edges"
    )
