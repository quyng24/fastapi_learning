"""
tests/conftest.py
==================
Test configuration và fixtures dùng chung.
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_db
from app.models import user, post  # noqa: F401 — Import để Base biết về các models

# ===================================
# Test Database (SQLite in-memory)
# ===================================
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Tạo SQLite in-memory engine cho toàn bộ test session."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """
    Database session cho mỗi test.
    
    Tự động rollback sau mỗi test → Tests không ảnh hưởng lẫn nhau.
    """
    TestingSessionLocal = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    
    async with TestingSessionLocal() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    HTTP test client với database được override.
    
    Override get_db dependency để dùng test database thay vì real database.
    """
    from app.main import create_app
    
    app = create_app()
    
    # Override database dependency
    async def override_get_db():
        yield db
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


# ===================================
# Helper Fixtures
# ===================================
@pytest_asyncio.fixture
async def test_user_data():
    """Data cho việc tạo test user."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPass123",
        "password_confirm": "TestPass123",
        "full_name": "Test User",
    }


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient, test_user_data: dict):
    """Tạo và trả về user đã đăng ký."""
    response = await client.post("/api/v1/users", json=test_user_data)
    assert response.status_code == 201
    return response.json()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, test_user_data: dict, registered_user: dict):
    """Lấy auth headers sau khi login."""
    response = await client.post("/api/v1/auth/login", json={
        "username": test_user_data["email"],
        "password": test_user_data["password"],
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

