"""
app/dependencies/auth.py
=========================
FastAPI Dependencies cho Authentication & Authorization.

DEPENDENCY INJECTION TRONG FASTAPI:
=====================================
FastAPI's Depends() là công cụ Dependency Injection (DI) tích hợp sẵn.

Cách hoạt động:
1. Bạn khai báo dependency là function với Depends()
2. FastAPI tự động gọi function đó và inject kết quả vào route handler
3. Dependencies có thể chain (dependency phụ thuộc vào dependency khác)

VÍ DỤ CHAIN DEPENDENCIES:
==========================
get_db()                           # Level 1: Tạo DB session
    ↓
get_current_user(db=Depends(get_db))  # Level 2: Dùng DB để lấy user
    ↓
get_current_active_user(user=Depends(get_current_user))  # Level 3: Check user active
    ↓
get_current_superuser(user=Depends(get_current_active_user))  # Level 4: Check admin

FastAPI tự động resolve toàn bộ chain này!
"""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import verify_token
from app.exceptions.user import (
    ForbiddenError,
    TokenExpiredError,
    UnauthorizedError,
    UserNotFoundError,
)
from app.models.user import User
from app.repositories.user import UserRepository

# HTTPBearer: Tự động parse "Authorization: Bearer <token>" header
# auto_error=False: Không tự động throw error, để ta xử lý manually
bearer_scheme = HTTPBearer(auto_error=False)


# ===================================
# Core Auth Dependency
# ===================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency: Lấy current user từ JWT token.
    
    Quá trình:
    1. Đọc JWT token từ Authorization header
    2. Verify token (signature, expiration)
    3. Lấy user_id từ token payload
    4. Query DB để lấy user object
    
    Raise:
        UnauthorizedError: Nếu không có token hoặc token invalid
        UserNotFoundError: Nếu user trong token không còn tồn tại
    """
    if not credentials:
        raise UnauthorizedError("Vui lòng đăng nhập để tiếp tục")
    
    # Verify và decode token
    payload = verify_token(credentials.credentials, token_type="access")
    
    if not payload:
        raise TokenExpiredError()
    
    # Lấy user_id từ "sub" claim
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError()
    
    try:
        user_id = int(user_id_str)
    except ValueError:
        raise UnauthorizedError()
    
    # Query user từ DB
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    
    if not user:
        raise UserNotFoundError(user_id)
    
    return user


# ===================================
# Role-based Dependencies
# ===================================
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency: Lấy current user và kiểm tra tài khoản active.
    
    Dùng cho hầu hết các protected endpoints.
    """
    if not current_user.is_active:
        raise ForbiddenError("Tài khoản của bạn đã bị vô hiệu hóa")
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency: Chỉ cho phép superuser.
    
    Dùng cho admin endpoints.
    """
    if not current_user.is_superuser:
        raise ForbiddenError("Chỉ superuser mới có quyền thực hiện thao tác này")
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Dependency: Yêu cầu user đã xác thực email.
    
    Dùng cho các tính năng cần email verified (ví dụ: đăng bài).
    """
    if not current_user.is_verified:
        raise ForbiddenError("Vui lòng xác thực email trước khi thực hiện thao tác này")
    return current_user


# ===================================
# Optional Auth (cho endpoints vừa public vừa private)
# ===================================
async def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Dependency: Trả về current user nếu có token, None nếu không.
    
    Dùng cho endpoints có behavior khác nhau tùy theo đã login hay chưa.
    Ví dụ: Xem bài viết (public), nhưng nếu đã login thì track view count.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials=credentials, db=db)
    except Exception:
        return None


# ===================================
# Service Dependencies
# ===================================
def get_user_service(db: AsyncSession = Depends(get_db)):
    """
    Dependency: Tạo UserService với dependencies đã inject.
    
    BẢNG HỌC: Đây là Composition Root pattern.
    Tất cả objects được "lắp ráp" ở đây, không phải trong service/repository.
    """
    from app.services.user import UserService
    user_repo = UserRepository(db)
    return UserService(user_repo)

