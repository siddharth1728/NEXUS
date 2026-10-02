"""Unit tests for database session and connection functions."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.core.config import DatabaseSettings
from app.db.session import (
    check_database_connection,
    close_database_connections,
    get_db,
    get_engine,
    get_session_factory,
)
from app.services.base import BaseService


@pytest.mark.asyncio
async def test_db_session_lifecycle():
    await close_database_connections()

    # Use SQLite in-memory setting
    custom_db_settings = DatabaseSettings(
        url="sqlite+aiosqlite:///:memory:",
        sync_url="sqlite:///:memory:",
    )

    # 1. Engine & session factory initialization
    engine = get_engine(custom_db_settings)
    assert engine is not None

    factory = get_session_factory(custom_db_settings)
    assert factory is not None

    # 2. Connection check
    is_ok, latency, err = await check_database_connection(engine)
    assert is_ok is True
    assert latency >= 0.0
    assert err is None

    # 3. get_db generator
    sessions: list[AsyncSession] = []
    async for sess in get_db():
        sessions.append(sess)
        assert isinstance(sess, AsyncSession)

    assert len(sessions) == 1

    # 4. Cleanup
    await close_database_connections()


@pytest.mark.asyncio
async def test_get_db_session_dep():
    await close_database_connections()
    custom_db_settings = DatabaseSettings(
        url="sqlite+aiosqlite:///:memory:",
        sync_url="sqlite:///:memory:",
    )
    get_engine(custom_db_settings)
    sessions = []
    async for s in get_db_session():
        sessions.append(s)
    assert len(sessions) == 1
    await close_database_connections()


def test_base_service():
    srv = BaseService()
    assert srv is not None
