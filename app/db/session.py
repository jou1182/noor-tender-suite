"""
Database session configuration.

Primary: asynchronous SQLAlchemy engine on PostgreSQL 16 + asyncpg for the
vector retrieval layer (models in ``app.db.models``).

Fallback: the legacy synchronous engine (SQLite in dev, psycopg2 for
PostgreSQL) used by the existing FastAPI endpoints and services.
"""

import os
from typing import AsyncGenerator, Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./contech.db")
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL", "")

# --- Async engine (PostgreSQL 16 + asyncpg) ---


def build_async_engine_url() -> str | None:
    """Derive the async URL from DATABASE_URL when ASYNC_DATABASE_URL is unset."""
    if ASYNC_DATABASE_URL:
        return ASYNC_DATABASE_URL
    if DATABASE_URL.startswith("postgresql://"):
        return DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
    # No async URL configured — async engine stays uninitialized (sync-only envs).
    return None


_async_engine = None


def get_async_engine():
    """Lazily build the async engine (requires asyncpg + a Postgres async URL)."""
    global _async_engine
    if _async_engine is None:
        url = build_async_engine_url()
        if url is None:
            raise RuntimeError(
                "Async engine requested but no ASYNC_DATABASE_URL / postgres DATABASE_URL configured."
            )
        from sqlalchemy.ext.asyncio import create_async_engine as _create

        _async_engine = _create(url, pool_pre_ping=True, pool_size=10, max_overflow=20)
    return _async_engine


def get_async_sessionmaker():
    """Lazily build the async session factory."""
    from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
    from sqlalchemy.ext.asyncio import async_sessionmaker as _async_sessionmaker

    return _async_sessionmaker(
        get_async_engine(), class_=_AsyncSession, expire_on_commit=False
    )


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async session (Postgres only)."""
    factory = get_async_sessionmaker()
    async with factory() as session:
        yield session


# --- Legacy sync engine (unchanged behavior) ---


if DATABASE_URL.startswith("postgresql"):
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
