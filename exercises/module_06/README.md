# Module 06 — Testing, Error Handling & Production

## 🎯 Mục Tiêu Module Này

Viết tests đúng chuẩn cho FastAPI, setup production-ready error handling và logging.

---

## 📖 Lý Thuyết

### Testing Pyramid

```
        /\
       /E2E\        ← Ít test nhất (chậm, expensive)
      /──────\       Selenium, Playwright
     / Integ  \     ← Vừa phải (test nhiều layers)
    /──────────\     TestClient + DB thật
   /  Unit Test \   ← Nhiều nhất (nhanh, isolated)
  /──────────────\   Mock dependencies
```

### 3 Loại Test trong FastAPI

```python
# 1. UNIT TEST — Test service/repository logic
async def test_user_service_register():
    # Mock repository
    mock_repo = AsyncMock()
    mock_repo.email_exists.return_value = False
    mock_repo.create.return_value = fake_user

    service = UserService(mock_repo)
    user = await service.register_user(valid_data)

    assert user.email == valid_data.email

# 2. INTEGRATION TEST — Test với real database
async def test_register_endpoint(client: AsyncClient, db: AsyncSession):
    response = await client.post("/api/v1/users", json={...})
    assert response.status_code == 201

    # Verify trong DB
    user_in_db = await UserRepository(db).get_by_email(data["email"])
    assert user_in_db is not None

# 3. E2E TEST — Test full flow
async def test_full_auth_flow(client):
    # 1. Register
    await client.post("/api/v1/users", json=register_data)
    # 2. Login
    token_response = await client.post("/api/v1/auth/login", json=login_data)
    token = token_response.json()["access_token"]
    # 3. Use token
    response = await client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
```

---

## 📝 BÀI TẬP

### Bài 6.1 — Setup Test Infrastructure (1 giờ)

**Yêu cầu:** Tạo `tests/conftest.py`:

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Dùng SQLite in-memory database cho tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Tạo test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Database session cho mỗi test (tự rollback sau test)."""
    async with AsyncSession(test_engine) as session:
        yield session
        await session.rollback()  # Clean slate sau mỗi test

@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """HTTP test client với database được override."""
    from app.main import create_app
    from app.core.database import get_db

    app = create_app()
    app.dependency_overrides[get_db] = lambda: db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
```

---

### Bài 6.2 — Unit Tests cho UserService (2 giờ)

**Yêu cầu:** Tạo `tests/unit/test_user_service.py`:

```python
# Viết tests cho:

class TestUserServiceRegister:
    async def test_register_success(self): ...
    async def test_register_duplicate_email_raises(self): ...
    async def test_register_duplicate_username_raises(self): ...
    async def test_password_is_hashed(self): ...

class TestUserServiceAuthenticate:
    async def test_login_success(self): ...
    async def test_login_wrong_password_raises(self): ...
    async def test_login_inactive_user_raises(self): ...
    async def test_login_nonexistent_user_raises(self): ...

class TestUserServiceUpdate:
    async def test_update_profile_success(self): ...
    async def test_update_with_none_fields_ignored(self): ...
    async def test_update_nonexistent_user_raises(self): ...
```

**Hint — Cách mock:**

```python
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_user_repo():
    repo = AsyncMock(spec=UserRepository)
    return repo

@pytest.fixture
def user_service(mock_user_repo):
    return UserService(mock_user_repo)

async def test_register_duplicate_email_raises(user_service, mock_user_repo):
    mock_user_repo.email_exists.return_value = True  # Simulate email exists

    with pytest.raises(EmailAlreadyExistsError):
        await user_service.register_user(UserCreate(
            email="existing@test.com",
            username="newuser",
            password="Password123",
            password_confirm="Password123",
        ))
```

---

### Bài 6.3 — Integration Tests cho API Endpoints (3 giờ)

**Yêu cầu:** Tạo `tests/integration/test_users_api.py`:

```python
class TestRegisterEndpoint:
    async def test_register_returns_201(self, client): ...
    async def test_register_returns_user_data(self, client): ...
    async def test_register_does_not_return_password(self, client): ...
    async def test_register_duplicate_email_returns_409(self, client): ...
    async def test_register_invalid_email_returns_422(self, client): ...
    async def test_register_weak_password_returns_422(self, client): ...

class TestAuthFlow:
    async def test_full_login_flow(self, client): ...
    async def test_invalid_login_returns_401(self, client): ...
    async def test_protected_endpoint_without_token_returns_401(self, client): ...
    async def test_protected_endpoint_with_valid_token_returns_200(self, client): ...
    async def test_expired_token_returns_401(self, client): ...

class TestUserEndpoints:
    async def test_get_me(self, client, auth_headers): ...
    async def test_update_profile(self, client, auth_headers): ...
    async def test_cannot_access_other_user_data(self, client, auth_headers): ...
```

---

### Bài 6.4 — Error Response Consistency (1 giờ)

**Yêu cầu:** Viết test đảm bảo TẤT CẢ error responses đều có format nhất quán:

```python
async def test_error_responses_have_consistent_format(client):
    """Mọi error response phải có fields: success, message, error_code"""

    error_scenarios = [
        # (HTTP method, URL, body, expected_status)
        ("GET", "/api/v1/users/99999", None, 404),
        ("POST", "/api/v1/users", {}, 422),
        ("POST", "/api/v1/auth/login", {"username": "wrong", "password": "wrong"}, 401),
        ("GET", "/api/v1/users", None, 401),  # No auth
    ]

    for method, url, body, expected_status in error_scenarios:
        response = await client.request(method, url, json=body)

        assert response.status_code == expected_status
        data = response.json()

        # Kiểm tra format nhất quán
        assert "success" in data
        assert data["success"] == False
        assert "message" in data
```

---

### Bài 6.5 — Structured Logging (2 giờ, nâng cao)

**Yêu cầu:** Implement structured logging thay thế print statements:

```python
# app/core/logging.py
import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Log theo format JSON để dễ parse bởi log aggregators (ELK, Datadog, etc.)"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Thêm extra context nếu có
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

def setup_logging(debug: bool = False):
    """Cấu hình logging cho ứng dụng."""
    level = logging.DEBUG if debug else logging.INFO

    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logger = logging.getLogger("app")
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

logger = setup_logging()
```

---

## ✅ Checklist

- [ ] Setup test infrastructure với test database
- [ ] Viết unit tests cho UserService
- [ ] Viết integration tests cho API endpoints
- [ ] Đảm bảo error response format nhất quán
- [ ] Test coverage >= 80%
- [ ] (Nâng cao) Implement structured JSON logging

---

## 🎉 HOÀN THÀNH TOÀN BỘ KHÓA HỌC!

Sau khi hoàn thành tất cả 6 modules, bạn đã nắm vững:

```
✅ Layered Architecture (Endpoint → Service → Repository → DB)
✅ Repository Pattern với Generic BaseRepository
✅ Service Layer với proper Business Logic
✅ Pydantic v2 Schemas (Request/Response DTOs)
✅ JWT Authentication với role-based authorization
✅ FastAPI Dependency Injection
✅ Custom Middleware
✅ Domain Exceptions & Global Error Handling
✅ Unit & Integration Testing
✅ Async SQLAlchemy 2.0
```

### 🚀 Bước Tiếp Theo

1. **Thêm Redis caching** — Cache expensive queries
2. **Background Tasks** — Celery + Redis cho async jobs
3. **WebSockets** — Real-time features
4. **Docker + Docker Compose** — Containerize ứng dụng
5. **CI/CD** — GitHub Actions pipeline
6. **Monitoring** — Prometheus + Grafana
