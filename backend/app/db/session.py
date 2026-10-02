"""NEXUS Database Session & Connection Management.

Provides async SQLAlchemy engine, session factories, and database connectivity checks.
"""

import time
from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import DatabaseSettings, get_settings
from app.core.logging import get_logger

logger = get_logger("db")

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(db_settings: DatabaseSettings | None = None) -> AsyncEngine:
    """Return or initialize global AsyncEngine singleton."""
    global _engine
    if _engine is None:
        settings = db_settings or get_settings().db
        # SQLite doesn't support pool_size/max_overflow arguments in create_async_engine
        if settings.url.startswith("sqlite"):
            _engine = create_async_engine(
                settings.url,
                echo=settings.echo,
            )
        else:
            _engine = create_async_engine(
                settings.url,
                echo=settings.echo,
                pool_size=settings.pool_size,
                max_overflow=settings.max_overflow,
                pool_timeout=settings.pool_timeout,
                pool_pre_ping=True,
            )
        logger.info("Initialized AsyncEngine")
    return _engine


def get_session_factory(
    db_settings: DatabaseSettings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return or initialize global async_sessionmaker singleton."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(db_settings)
        _session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session with automatic transaction management."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def check_database_connection(
    engine: AsyncEngine | None = None,
) -> tuple[bool, float, str | None]:
    """Check database liveness by executing a ping query.

    Returns:
        (is_healthy, latency_ms, error_message)
    """
    target_engine = engine or get_engine()
    start = time.perf_counter()
    try:
        async with target_engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = (time.perf_counter() - start) * 1000.0
        return True, latency_ms, None
    except Exception as exc:
        latency_ms = (time.perf_counter() - start) * 1000.0
        logger.warning(f"Database readiness probe failed: {exc}")
        return False, latency_ms, str(exc)


async def close_database_connections() -> None:
    """Dispose of engine connections on application shutdown."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Disposed database engine connections")
