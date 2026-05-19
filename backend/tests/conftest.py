import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.db import Base, get_session
from app.main import app
from app.models.user import User  # noqa: F401 — для регистрации моделей
from app.models.query import Query  # noqa: F401
from app.models.tracked import TrackedItem, PriceHistory  # noqa: F401
from app.models.subscription import Subscription  # noqa: F401

# SQLite in-memory с одним соединением (StaticPool) — все сессии видят одну БД
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db_engine):
    session_maker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_session() -> AsyncSession:
        async with session_maker() as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    # Сбрасываем in-memory сессии и rate limiter между тестами
    from app.api import deps, search as search_api
    deps._fake_sessions.clear()
    search_api._rate_counters.clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
