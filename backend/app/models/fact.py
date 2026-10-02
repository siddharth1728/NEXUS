"""Fact model for structured information extraction."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.document import Document, DocumentChunk
    from app.models.tenant import Tenant


class Fact(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A Fact represents a discrete piece of source-grounded information."""

    __tablename__ = "facts"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("document_chunks.id"), nullable=True, index=True
    )

    statement: Mapped[str] = mapped_column(Text, nullable=False)
    verbatim_quote: Mapped[str] = mapped_column(Text, nullable=False)

    # E.g. HIGH, MEDIUM, REQUIRES_REVIEW, UNKNOWN, CONFLICT
    confidence: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)

    metadata_: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSON, default=dict, nullable=False
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant")
    document: Mapped["Document"] = relationship("Document", foreign_keys=[document_id])
    chunk: Mapped["DocumentChunk | None"] = relationship("DocumentChunk", foreign_keys=[chunk_id])
