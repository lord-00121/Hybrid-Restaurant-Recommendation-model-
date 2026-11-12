"""SQLAlchemy async database engine and session management.

Replaces the previous Motor/MongoDB layer. Works with any SQLAlchemy-supported
backend via DATABASE_URL:
  - sqlite+aiosqlite:///./hybrid_rec.db   (local dev default)
  - postgresql+asyncpg://user:pass@host/db (production, e.g. Neon / Render Postgres)
"""

import sys
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Ensure current directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from config import settings
from models.db_models import Base


def _sanitize_url(url: str) -> str:
    """Strip query params that SQLAlchemy asyncpg/psycopg drivers reject.

    Neon connection strings often include sslmode/channel_binding which
    asyncpg.connect() does not accept. SSL is still used by default.
    """
    if "?" not in url:
        return url
    base, _, query = url.partition("?")
    kept = [
        p for p in query.split("&")
        if p and not p.lower().startswith(("sslmode=", "channel_binding="))
    ]
    return base + ("?" + "&".join(kept) if kept else "")


DATABASE_URL = _sanitize_url(settings.DATABASE_URL)

# Async engine — echo=False for clean logs
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    # SQLite needs this for concurrent writes; harmless on Postgres
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create all tables if they do not exist (idempotent)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_sync_session_factory():
    """Synchronous session factory for standalone scripts (seed, evaluation).

    Uses a sync engine derived from DATABASE_URL by swapping the async driver
    for its synchronous counterpart.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    url = DATABASE_URL
    if url.startswith("sqlite+aiosqlite"):
        sync_url = url.replace("sqlite+aiosqlite", "sqlite")
    elif url.startswith("postgresql+asyncpg"):
        sync_url = url.replace("postgresql+asyncpg", "postgresql+psycopg")
    else:
        sync_url = url

    sync_engine = create_engine(sync_url)
    return sessionmaker(bind=sync_engine, expire_on_commit=False)
