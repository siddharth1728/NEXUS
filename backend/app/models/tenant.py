"""Tenant Model."""

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.action import Action
    from app.models.document import Document
    from app.models.user import User


class Tenant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """A Tenant represents an organizational boundary in NEXUS."""

    __tablename__ = "tenants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    users: Mapped[list["User"]] = relationship(
        "User", back_populates="tenant", cascade="all, delete-orphan"
    )
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="tenant", cascade="all, delete-orphan"
    )
    actions: Mapped[list["Action"]] = relationship(
        "Action", back_populates="tenant", cascade="all, delete-orphan"
    )
