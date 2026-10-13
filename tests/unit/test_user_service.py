"""
tests/unit/test_user_service.py
================================
Unit tests cho UserService.

NGUYÊN TẮC UNIT TEST:
- Test một đơn vị nhỏ (function/method)
- Mock tất cả dependencies
- Nhanh (không cần DB, network)
- Isolated (tests không ảnh hưởng nhau)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from app.schemas.user import UserCreate, UserUpdate
from app.services.user import UserService


# ===================================
# Test Fixtures
# ===================================
@pytest.fixture
def mock_user_repo():
    """Mock UserRepository để isolate tests khỏi database."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def user_service(mock_user_repo):
    """UserService với mock repository."""
    return UserService(mock_user_repo)


@pytest.fixture
def valid_user_create():
    """Valid UserCreate data."""
    return UserCreate(
        email="newuser@test.com",
        username="newuser",
        password="TestPass123",
        password_confirm="TestPass123",
        full_name="New User",
    )


@pytest.fixture
def fake_user():
    """Fake User object (không cần DB thật)."""
    user = MagicMock()
    user.id = 1
    user.email = "newuser@test.com"
    user.username = "newuser"
    user.full_name = "New User"
    user.is_active = True
    user.is_verified = False
    user.is_superuser = False
    user.hashed_password = "$2b$12$fake_hashed_password"
    return user


# ===================================
# Test: register_user()
# ===================================
class TestRegisterUser:
    
    @pytest.mark.asyncio
    async def test_register_success(
        self,
        user_service: UserService,
        mock_user_repo,
        valid_user_create: UserCreate,
        fake_user,
    ):
        """Test đăng ký thành công."""
        # Setup mocks
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.username_exists.return_value = False
        mock_user_repo.create.return_value = fake_user
        
        # Act
        result = await user_service.register_user(valid_user_create)
        
        # Assert
        assert result == fake_user
        mock_user_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises(
        self,
        user_service: UserService,
        mock_user_repo,
        valid_user_create: UserCreate,
    ):
        """Test đăng ký với email đã tồn tại → raise EmailAlreadyExistsError."""
        mock_user_repo.email_exists.return_value = True
        
        with pytest.raises(EmailAlreadyExistsError) as exc_info:
            await user_service.register_user(valid_user_create)
        
        assert "newuser@test.com" in str(exc_info.value)
        mock_user_repo.create.assert_not_called()  # Không tạo user khi email duplicate
    
    @pytest.mark.asyncio
    async def test_register_duplicate_username_raises(
        self,
        user_service: UserService,
        mock_user_repo,
        valid_user_create: UserCreate,
    ):
        """Test đăng ký với username đã tồn tại → raise UsernameAlreadyExistsError."""
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.username_exists.return_value = True
        
        with pytest.raises(UsernameAlreadyExistsError):
            await user_service.register_user(valid_user_create)
    
    @pytest.mark.asyncio
    async def test_password_is_hashed_before_save(
        self,
        user_service: UserService,
        mock_user_repo,
        valid_user_create: UserCreate,
        fake_user,
    ):
        """Test password được hash trước khi lưu (không lưu plain text)."""
        mock_user_repo.email_exists.return_value = False
        mock_user_repo.username_exists.return_value = False
        mock_user_repo.create.return_value = fake_user
        
        await user_service.register_user(valid_user_create)
        
        # Lấy args được truyền vào create()
        create_call_args = mock_user_repo.create.call_args[0][0]
        
        # Password phải được hash, không phải plain text
        assert create_call_args["hashed_password"] != valid_user_create.password
        assert create_call_args["hashed_password"].startswith("$2b$")  # bcrypt prefix


# ===================================
# Test: authenticate()
# ===================================
class TestAuthenticate:
    
    @pytest.mark.asyncio
    async def test_login_nonexistent_user_raises(
        self,
        user_service: UserService,
        mock_user_repo,
    ):
        """Test login với user không tồn tại → raise InvalidCredentialsError."""
        mock_user_repo.get_by_email_or_username.return_value = None
        
        from app.schemas.common import LoginRequest
        credentials = LoginRequest(username="nonexistent", password="Pass123")
        
        with pytest.raises(InvalidCredentialsError):
            await user_service.authenticate(credentials)
    
    @pytest.mark.asyncio
    async def test_login_inactive_user_raises(
        self,
        user_service: UserService,
        mock_user_repo,
        fake_user,
    ):
        """Test login với tài khoản inactive → raise InvalidCredentialsError."""
        fake_user.is_active = False
        mock_user_repo.get_by_email_or_username.return_value = fake_user
        
        from app.schemas.common import LoginRequest
        credentials = LoginRequest(username="test@test.com", password="Pass123")
        
        with pytest.raises(InvalidCredentialsError):
            await user_service.authenticate(credentials)

