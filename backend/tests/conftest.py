"""NEXUS Test Configuration & Fixtures."""

import os

os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import AppEnvironment, DatabaseSettings, Settings
from app.main import create_app
from app.models.base import Base


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Provide isolated test application settings."""
    return Settings(
        app_name="NEXUS Test Engine",
        app_version="0.1.0-test",
        env=AppEnvironment.TESTING,
        debug=True,
        log_level="DEBUG",
        log_json=False,
        db=DatabaseSettings(
            url="sqlite+aiosqlite:///:memory:",
            sync_url="sqlite:///:memory:",
            echo=False,
        ),
    )


@pytest.fixture
def test_app(test_settings: Settings) -> None:
    """Create a FastAPI application configured for testing."""
    app = create_app(test_settings)
    return app  # type: ignore


@pytest_asyncio.fixture
async def async_client(test_app) -> AsyncGenerator[AsyncClient, None]:  # type: ignore
    """Provide asynchronous HTTP client for testing API endpoints."""
    transport = ASGITransport(app=test_app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def in_memory_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide in-memory SQLite async database session for unit testing repositories."""
    engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()
