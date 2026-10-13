"""
app/api/v1/endpoints/users.py
==============================
Router/Endpoint Layer cho User resources.

ENDPOINT LAYER LÀM GÌ?
=======================
Endpoint layer CHỈ xử lý HTTP concerns:
- Parse request body/query params
- Gọi service với data đã được parse
- Format và trả về response

Endpoint KHÔNG nên chứa business logic!
Business logic thuộc về Service layer.

HTTP METHOD → CRUD MAPPING:
============================
GET    /users          → list users (index)
POST   /users          → create user
GET    /users/{id}     → get one user
PUT    /users/{id}     → replace user (full update)
PATCH  /users/{id}     → partial update user
DELETE /users/{id}     → delete user
"""

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import (
    get_current_active_user,
    get_current_superuser,
    get_user_service,
)
from app.models.user import User
from app.schemas.common import PagedResponse, PaginationParams, SuccessResponse
from app.schemas.user import UserCreate, UserPublicResponse, UserResponse, UserUpdate
from app.services.user import UserService

router = APIRouter(prefix="/users", tags=["Users"])


# ===================================
# PUBLIC ENDPOINTS (Không cần auth)
# ===================================
@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Đăng ký tài khoản mới",
    description="""
    Tạo tài khoản người dùng mới.
    
    **Yêu cầu:**
    - Email và username phải unique
    - Password tối thiểu 8 ký tự, có chữ hoa, chữ thường, số
    """,
)
async def register(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    """
    BẢNG HỌC: Endpoint này:
    1. Nhận UserCreate schema (Pydantic validate tự động)
    2. Gọi service.register_user() (business logic)
    3. Trả về UserResponse (serialize + ẩn sensitive fields)
    
    Nếu email/username đã tồn tại → service raise exception → handler trả về 409
    """
    new_user = await service.register_user(user_data)
    return new_user


@router.get(
    "/{user_id}/profile",
    response_model=UserPublicResponse,
    summary="Xem profile public của user",
)
async def get_public_profile(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Endpoint public - ai cũng xem được, không cần auth."""
    user = await service.get_user_by_id(user_id)
    return user


# ===================================
# PROTECTED ENDPOINTS (Cần auth)
# ===================================
@router.get(
    "",
    response_model=PagedResponse[UserResponse],
    summary="Danh sách users (chỉ admin)",
    dependencies=[Depends(get_current_superuser)],  # Shorthand: chỉ check permission, không inject
)
async def list_users(
    page: int = Query(default=1, ge=1, description="Trang hiện tại"),
    page_size: int = Query(default=20, ge=1, le=100, description="Số items mỗi trang"),
    service: UserService = Depends(get_user_service),
):
    """
    BẢNG HỌC: dependencies=[Depends(get_current_superuser)]
    Cách viết tắt khi chỉ cần check permission mà không cần inject user object.
    """
    pagination = PaginationParams(page=page, page_size=page_size)
    return await service.get_users_paginated(pagination)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Lấy thông tin user hiện tại",
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
):
    """
    Endpoint cho phép user xem thông tin của chính mình.
    
    BẢNG HỌC: `current_user` được inject tự động qua dependency chain:
    Depends(get_current_active_user) → Depends(get_current_user) → Query DB
    """
    return current_user


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Cập nhật profile của mình",
)
async def update_my_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    service: UserService = Depends(get_user_service),
):
    """
    Partial update profile.
    Chỉ update các fields được gửi lên (không gửi → không thay đổi).
    """
    updated_user = await service.update_profile(current_user.id, update_data)
    return updated_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Lấy thông tin user theo ID (chỉ admin)",
    dependencies=[Depends(get_current_superuser)],
)
async def get_user_by_id(
    user_id: int,
    service: UserService = Depends(get_user_service),
):
    """Admin endpoint để xem thông tin chi tiết của bất kỳ user nào."""
    user = await service.get_user_by_id(user_id)
    return user


@router.delete(
    "/{user_id}",
    response_model=SuccessResponse,
    summary="Vô hiệu hóa tài khoản user (chỉ admin)",
)
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_superuser),
    service: UserService = Depends(get_user_service),
):
    """Admin endpoint để vô hiệu hóa tài khoản user."""
    await service.deactivate_user(user_id, admin_id=current_user.id)
    return SuccessResponse(message=f"Đã vô hiệu hóa tài khoản user #{user_id}")

