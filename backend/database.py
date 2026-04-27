"""
HealthVault AI — Database Engine & Session Management
Uses SQLAlchemy async engine with PostgreSQL (Supabase).
"""
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


# ── Engine ────────────────────────────────────────────────────────────────────

def _normalize_async_url(url: str) -> str:
    """
    Ensure the DATABASE_URL uses the asyncpg driver.
    Supabase/Heroku/Render typically hand out `postgresql://` or `postgres://`,
    but SQLAlchemy's async engine needs `postgresql+asyncpg://`.
    Also strips query params that asyncpg does not support (e.g. `sslmode`,
    `pgbouncer`) — TLS is negotiated automatically by asyncpg against Supabase.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Drop unsupported query params (asyncpg rejects sslmode / pgbouncer)
    if "?" in url:
        base, _, query = url.partition("?")
        kept = [
            p for p in query.split("&")
            if p and not p.lower().startswith(("sslmode=", "pgbouncer=", "channel_binding="))
        ]
        url = base + (f"?{'&'.join(kept)}" if kept else "")
    return url


engine = create_async_engine(
    _normalize_async_url(settings.DATABASE_URL),
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,          # recycles stale connections
    echo=not settings.is_production,
    # Supabase pooler (PgBouncer in transaction mode) does not support
    # prepared statements that persist across transactions. Disable asyncpg's
    # statement cache and randomize statement names so pooled connections
    # don't collide on names like "__asyncpg_stmt_8__".
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid.uuid4()}__",
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ── Base model ────────────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a DB session per request."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager version for use outside FastAPI (e.g., scheduler)."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
