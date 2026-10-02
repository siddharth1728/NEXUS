"""Unit tests for JWT authentication and dependencies."""

import uuid
from datetime import timedelta

import jwt
import pytest
from fastapi import HTTPException, status

from app.api.deps import get_current_tenant_id
from app.core.auth import create_access_token, verify_access_token
from app.core.config import DatabaseSettings, Settings


@pytest.fixture
def auth_settings():  # type: ignore
    from app.core.config import SecuritySettings
    return Settings(
        APP_ENV="production",
        security=SecuritySettings(secret_key="test-secret-key-that-is-very-long-and-secure-enough-32-chars"),
        db=DatabaseSettings(url="postgresql+asyncpg://nexus:test@localhost:5432/nexus_db"),
    )


def test_create_and_verify_access_token(auth_settings: Settings) -> None:
    subject = "user1"
    tenant_id = str(uuid.uuid4())

    token = create_access_token(subject, tenant_id, auth_settings)
    assert isinstance(token, str)

    payload = verify_access_token(token, auth_settings)
    assert payload["sub"] == subject
    assert payload["tenant_id"] == tenant_id


def test_verify_access_token_expired(auth_settings: Settings) -> None:
    subject = "user1"
    tenant_id = str(uuid.uuid4())

    token = create_access_token(subject, tenant_id, auth_settings, expires_delta=timedelta(seconds=-1))

    with pytest.raises(HTTPException) as exc:
        verify_access_token(token, auth_settings)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Token has expired"


def test_verify_access_token_invalid(auth_settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc:
        verify_access_token("invalid.token.string", auth_settings)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Could not validate credentials"


def test_verify_access_token_invalid_signature(auth_settings: Settings) -> None:
    subject = "user1"
    tenant_id = str(uuid.uuid4())

    from app.core.config import SecuritySettings
    # Sign with different secret
    other_settings = Settings(
        security=SecuritySettings(secret_key="different-secret-key-that-is-long-enough")
    )
    token = create_access_token(subject, tenant_id, other_settings)

    with pytest.raises(HTTPException) as exc:
        verify_access_token(token, auth_settings)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Could not validate credentials"


def test_get_current_tenant_id_valid(auth_settings: Settings) -> None:
    tenant_id = str(uuid.uuid4())
    token = create_access_token("user1", tenant_id, auth_settings)

    result = get_current_tenant_id(token=token, settings=auth_settings)
    assert str(result) == tenant_id


def test_get_current_tenant_id_missing_tenant(auth_settings: Settings) -> None:
    token = jwt.encode(
        {"sub": "user1", "exp": 9999999999},
        auth_settings.security.secret_key,
        algorithm=auth_settings.security.algorithm
    )
    with pytest.raises(HTTPException) as exc:
        get_current_tenant_id(token=token, settings=auth_settings)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "missing tenant_id" in exc.value.detail


def test_get_current_tenant_id_invalid_format(auth_settings: Settings) -> None:
    token = create_access_token("user1", "not-a-uuid", auth_settings)
    with pytest.raises(HTTPException) as exc:
        get_current_tenant_id(token=token, settings=auth_settings)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Invalid tenant_id format" in exc.value.detail


def test_get_current_tenant_id_no_token_prod(auth_settings: Settings) -> None:
    with pytest.raises(HTTPException) as exc:
        get_current_tenant_id(token="", settings=auth_settings)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert "Not authenticated" in exc.value.detail


def test_get_current_tenant_id_no_token_dev() -> None:
    dev_settings = Settings(APP_ENV="development")
    result = get_current_tenant_id(token="", settings=dev_settings)
    assert str(result) == "00000000-0000-4000-8000-000000000001"
