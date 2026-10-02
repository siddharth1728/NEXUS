"""Authentication and JWT operations."""
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException, status

from app.core.config import Settings


def create_access_token(
    subject: str,
    tenant_id: str,
    settings: Settings,
    expires_delta: timedelta | None = None
) -> str:
    """Create a new JWT access token."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.security.access_token_expire_minutes
        )

    to_encode = {
        "exp": expire,
        "sub": subject,
        "tenant_id": tenant_id
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.security.secret_key,
        algorithm=settings.security.algorithm
    )
    return encoded_jwt


def verify_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """Verify a JWT access token and return its payload."""
    try:
        payload = jwt.decode(
            token,
            settings.security.secret_key,
            algorithms=[settings.security.algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
