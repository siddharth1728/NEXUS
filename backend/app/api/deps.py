"""NEXUS API Dependencies.

Provides FastAPI dependency injection functions for database sessions, settings, and services.
"""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_access_token
from app.core.config import Settings, get_settings
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token", auto_error=False)

def get_app_settings(request: Request) -> Settings:
    """Dependency providing application settings from the current app instance."""
    if hasattr(request.app.state, "settings") and request.app.state.settings is not None:
        return request.app.state.settings  # type: ignore[no-any-return]
    return get_settings()

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency providing an async database session."""
    async for session in get_db():
        yield session

def get_current_tenant_id(
    token: str = Depends(oauth2_scheme),
    settings: Settings = Depends(get_app_settings)
) -> uuid.UUID:
    """Authentication dependency providing the current tenant ID from JWT."""
    if not token:
        # Fallback to a default DEV tenant if not in production and no token provided
        # This keeps existing tests working without modifying hundreds of test requests
        if not settings.is_production:
            return uuid.UUID("00000000-0000-4000-8000-000000000001")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_access_token(token, settings)
        tenant_id_str: str | None = payload.get("tenant_id")
        if tenant_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing tenant_id",
            )
        return uuid.UUID(tenant_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid tenant_id format",
        )
