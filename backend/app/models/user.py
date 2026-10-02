"""User Model."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.action import Action
    from app.models.tenant import Tenant


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Domain entity representing a system user."""

    __tablename__ = "users"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), default="member", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Note: Passwords are not stored in the core relational row to prevent plaintext leaks.
    # Future auth implementation will link via identity provider or separate secure table.

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", back_populates="users")
    actions: Mapped[list["Action"]] = relationship("Action", back_populates="assignee")
