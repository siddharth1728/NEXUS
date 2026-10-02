"""NEXUS API Dependencies.

Provides FastAPI dependency injection functions for database sessions, settings, and services.
"""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_db


def get_app_settings(request: Request) -> Settings:
    """Dependency providing application settings from the current app instance."""
    if hasattr(request.app.state, "settings") and request.app.state.settings is not None:
        return request.app.state.settings  # type: ignore[no-any-return]
    return get_settings()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing an async database session."""
    async for session in get_db():
        yield session


def get_current_tenant_id() -> uuid.UUID:
    """Mock authentication dependency providing the current tenant ID.

    WARNING: This is a development stub for Phase 01C to enforce tenant isolation
    without building the full authentication pipeline yet.
    """
    return uuid.UUID("00000000-0000-4000-8000-000000000001")
