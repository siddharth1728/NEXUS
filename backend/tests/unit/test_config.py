"""Unit tests for configuration loading and validation."""

import pytest
from pydantic import ValidationError

from app.core.config import AppEnvironment, DatabaseSettings, Settings, get_settings


def test_default_settings() -> None:
    settings = Settings()
    assert settings.app_name == "NEXUS Engine"
    assert settings.env == AppEnvironment.DEVELOPMENT
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.is_production is False
    assert settings.is_testing is False
    assert settings.db.pool_size == 10
    assert settings.ai.default_provider == "gemini"

def test_environment_flags() -> None:
    prod_settings = Settings(APP_ENV="production", db=DatabaseSettings(url="postgresql+asyncpg://nexus:test@localhost:5432/nexus_db"))
    assert prod_settings.is_production is True
    assert prod_settings.is_testing is False

    test_settings = Settings(APP_ENV="testing")
    assert test_settings.is_production is False
    assert test_settings.is_testing is True


def test_invalid_log_level() -> None:
    with pytest.raises(ValidationError):
        Settings(LOG_LEVEL="INVALID_LEVEL")


def test_valid_log_level_case_insensitivity() -> None:
    settings = Settings(LOG_LEVEL="debug")
    assert settings.log_level == "DEBUG"


def test_cached_get_settings() -> None:
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
