"""
app/api/v1/endpoints/auth.py
=============================
Authentication Endpoints — Login, Logout, Refresh Token.
"""

from fastapi import APIRouter, Depends, status

from app.core.security import create_access_token, create_refresh_token, verify_token
from app.dependencies.auth import get_current_active_user, get_user_service
from app.exceptions.user import InvalidCredentialsError, TokenExpiredError, UnauthorizedError
from app.models.user import User
from app.schemas.common import LoginRequest, RefreshTokenRequest, SuccessResponse, TokenResponse
from app.services.user import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Đăng nhập",
    description="Đăng nhập bằng username/email và password. Trả về JWT tokens.",
)
async def login(
    credentials: LoginRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Login flow:
    1. Validate credentials
    2. Authenticate user (service layer)
    3. Tạo access token + refresh token
    4. Trả về tokens
    
    SECURITY: Luôn trả về 401 khi sai credentials, không tiết lộ chi tiết.
    """
    from app.core.config import settings
    
    user = await service.authenticate(credentials)
    
    # Tạo tokens
    access_token = create_access_token(
        subject=str(user.id),
        additional_claims={
            "username": user.username,
            "is_superuser": user.is_superuser,
        }
    )
    refresh_token = create_refresh_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Lấy access token mới bằng refresh token",
)
async def refresh_token(
    token_data: RefreshTokenRequest,
    service: UserService = Depends(get_user_service),
):
    """
    Refresh token flow:
    1. Verify refresh token
    2. Lấy user từ token
    3. Tạo access token mới
    4. Trả về tokens mới
    """
    from app.core.config import settings
    
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    
    if not payload:
        raise TokenExpiredError()
    
    user_id = int(payload.get("sub", 0))
    user = await service.get_user_by_id(user_id)
    
    if not user.is_active:
        raise UnauthorizedError()
    
    # Tạo tokens mới
    access_token = create_access_token(subject=str(user.id))
    new_refresh_token = create_refresh_token(subject=str(user.id))
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    summary="Đăng xuất",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
):
    """
    Logout endpoint.
    
    BẢNG HỌC: Với stateless JWT, server không thể "invalidate" token.
    Giải pháp trong production:
    1. Client xóa token khỏi storage (frontend)
    2. Lưu token vào Redis blacklist (server) → Check blacklist khi verify token
    3. Dùng short-lived tokens + refresh token rotation
    
    Implementation đơn giản ở đây: Client tự xử lý.
    """
    # TODO: Add token to Redis blacklist
    # await redis.setex(f"blacklist:{token}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, "1")
    
    return SuccessResponse(
        message=f"Đã đăng xuất thành công. Tạm biệt {current_user.username}!"
    )

