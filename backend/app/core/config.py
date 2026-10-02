"""NEXUS Core Configuration Module.

Provides typed, environment-driven configuration across all application subsystems
using Pydantic Settings.
"""

from enum import StrEnum
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnvironment(StrEnum):
    """Application runtime environment."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class DatabaseSettings(BaseSettings):
    """PostgreSQL and pgvector connection settings."""

    url: str = Field(
        default="sqlite+aiosqlite:///nexus.db",
        alias="DATABASE_URL",
        description="Async PostgreSQL connection URI",
    )
    sync_url: str | None = Field(
        default="postgresql://nexus:nexus_password@localhost:5432/nexus_db",
        alias="DATABASE_SYNC_URL",
        description="Synchronous PostgreSQL connection URI for Alembic migrations",
    )
    echo: bool = Field(default=False, alias="DB_ECHO")
    pool_size: int = Field(default=10, alias="DB_POOL_SIZE", ge=1, le=100)
    max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW", ge=0, le=100)
    pool_timeout: float = Field(default=30.0, alias="DB_POOL_TIMEOUT", ge=1.0)

    model_config = SettingsConfigDict(env_prefix="DB_", populate_by_name=True, extra="ignore")


class RedisSettings(BaseSettings):
    """Redis cache and task queue settings."""

    url: str | None = Field(
        default="redis://localhost:6379/0",
        alias="REDIS_URL",
        description="Redis connection URI",
    )
    socket_timeout: float = Field(default=5.0, alias="REDIS_TIMEOUT")
    enabled: bool = Field(default=True, alias="REDIS_ENABLED")

    model_config = SettingsConfigDict(env_prefix="REDIS_", populate_by_name=True, extra="ignore")


class AISettings(BaseSettings):
    """AI and LLM Provider configuration."""

    default_provider: Literal["gemini", "ollama", "huggingface", "mock"] = Field(
        default="gemini",
        alias="DEFAULT_LLM_PROVIDER",
    )
    gemini_api_key: str | None = Field(default=None, alias="GEMINI_API_KEY")
    gemini_model_default: str = Field(default="gemini-1.5-pro", alias="GEMINI_MODEL_DEFAULT")
    gemini_model_fast: str = Field(default="gemini-1.5-flash", alias="GEMINI_MODEL_FAST")
    ollama_base_url: str = Field(default="http://localhost:11434", alias="OLLAMA_BASE_URL")
    ollama_model_default: str = Field(default="llama3:8b", alias="OLLAMA_MODEL_DEFAULT")
    huggingface_api_token: str | None = Field(default=None, alias="HUGGINGFACE_API_TOKEN")

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")


class SecuritySettings(BaseSettings):
    """Security, JWT and authorization settings."""

    secret_key: str = Field(
        default="nexus-insecure-dev-secret-key-change-in-production-32chars",
        alias="APP_SECRET_KEY",
        min_length=32,
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")


class ObservabilitySettings(BaseSettings):
    """Tracing, Metrics, and Langfuse configuration."""

    langfuse_public_key: str | None = Field(default=None, alias="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str | None = Field(default=None, alias="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field(default="https://cloud.langfuse.com", alias="LANGFUSE_HOST")
    otel_endpoint: str | None = Field(default=None, alias="OTEL_EXPORTER_OTLP_ENDPOINT")

    model_config = SettingsConfigDict(populate_by_name=True, extra="ignore")


class Settings(BaseSettings):
    """Root Application Settings aggregating all subsystem configs."""

    # Application
    app_name: str = "NEXUS Engine"
    app_version: str = "0.1.0"
    env: AppEnvironment = Field(default=AppEnvironment.DEVELOPMENT, alias="APP_ENV")
    debug: bool = Field(default=False, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=False, alias="LOG_JSON")

    # Subsystem Settings
    db: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    ai: AISettings = Field(default_factory=AISettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper_v = v.upper()
        if upper_v not in valid_levels:
            raise ValueError(f"Invalid LOG_LEVEL '{v}'. Must be one of {valid_levels}")
        return upper_v

    @property
    def is_production(self) -> bool:
        return self.env == AppEnvironment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        return self.env == AppEnvironment.TESTING

    @model_validator(mode="after")
    def validate_production_db(self) -> "Settings":
        if self.is_production and self.db.url.startswith("sqlite"):
            raise ValueError(
                "SQLite is strictly prohibited in PRODUCTION environments. "
                "You must provide a valid PostgreSQL connection URI with pgvector support."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
