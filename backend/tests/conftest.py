"""
HealthVault AI — Test Configuration & Fixtures
Uses an in-memory SQLite database for fast, isolated tests.
"""
import asyncio
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database import Base, get_db
from main import app
from models.user import User

# ── In-memory test DB ──────────────────────────────────────────────────────────

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_test_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


# ── Override DB dependency ─────────────────────────────────────────────────────

async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with TestSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


# ── Test user fixture ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    user = User(
        supabase_uid=uuid.uuid4(),
        email="test@healthvault.ai",
        full_name="Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ── Auth mock ──────────────────────────────────────────────────────────────────

from middleware.auth import get_current_user


def make_auth_override(user: User):
    async def _override():
        return user
    return _override


# ── HTTP client fixture ────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def client(test_user: User) -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_current_user] = make_auth_override(test_user)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_current_user, None)
