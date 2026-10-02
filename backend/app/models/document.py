"""Document and ExtractionJob Models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import ExtractionJobStatus

if TYPE_CHECKING:
    from app.models.action import Action
    from app.models.fact import Fact
    from app.models.tenant import Tenant
    from app.models.user import User


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A Document represents an ingested source of information."""

    __tablename__ = "documents"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    source_type: Mapped[str] = mapped_column(
        String(64), nullable=False
    )  # e.g., pdf, docx, slack, email
    source_uri: Mapped[str | None] = mapped_column(String, nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    raw_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    processing_status: Mapped[str] = mapped_column(String(32), default="PENDING", nullable=False)

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="documents")
    owner: Mapped["User | None"] = relationship("User")
    extraction_jobs: Mapped[list["ExtractionJob"]] = relationship(
        "ExtractionJob", back_populates="document", cascade="all, delete-orphan"
    )
    actions: Mapped[list["Action"]] = relationship("Action", back_populates="source_document")
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        "DocumentChunk", back_populates="document", cascade="all, delete-orphan"
    )
    facts: Mapped[list["Fact"]] = relationship(
        "Fact", back_populates="document", cascade="all, delete-orphan"
    )


class ExtractionJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Persistence representation of document-processing work."""

    __tablename__ = "extraction_jobs"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[ExtractionJobStatus] = mapped_column(
        String(32), default=ExtractionJobStatus.PENDING, nullable=False, index=True
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    error_category: Mapped[str | None] = mapped_column(String(255), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="extraction_jobs")


class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Normalized structural chunk of a parsed document."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )

    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)

    # E.g., title, heading, paragraph, table, list
    structural_type: Mapped[str] = mapped_column(String(64), nullable=False, default="paragraph")

    # Source Location Abstraction (page, section, block index)
    source_location: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # General metadata (e.g. parent heading text, parser version)
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="chunks")
    facts: Mapped[list["Fact"]] = relationship(
        "Fact", back_populates="chunk", cascade="all, delete-orphan"
    )
