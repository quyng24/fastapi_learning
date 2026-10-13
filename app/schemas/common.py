"""
app/schemas/common.py
======================
Schemas dùng chung cho toàn ứng dụng.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

# TypeVar để dùng với Generic
DataType = TypeVar("DataType")


# ===================================
# Pagination Schema
# ===================================
class PaginationParams(BaseModel):
    """
    Query params cho pagination.
    
    Dùng như Dependency:
    @router.get("/users")
    async def list_users(pagination: PaginationParams = Depends()):
        skip = pagination.skip
        limit = pagination.limit
    """
    page: int = Field(default=1, ge=1, description="Trang hiện tại (bắt đầu từ 1)")
    page_size: int = Field(default=20, ge=1, le=100, description="Số items mỗi trang (tối đa 100)")
    
    @property
    def skip(self) -> int:
        """Tính offset để dùng trong DB query."""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Alias cho page_size."""
        return self.page_size


class PagedResponse(BaseModel, Generic[DataType]):
    """
    Response wrapper cho danh sách có pagination.
    
    Generic[DataType] cho phép tái sử dụng với bất kỳ data type nào.
    
    Ví dụ:
        PagedResponse[UserResponse]  → list users
        PagedResponse[PostResponse]  → list posts
    
    Response structure:
    {
        "items": [...],
        "total": 100,
        "page": 1,
        "page_size": 20,
        "total_pages": 5,
        "has_next": true,
        "has_prev": false
    }
    """
    items: list[DataType]
    total: int = Field(description="Tổng số records")
    page: int = Field(description="Trang hiện tại")
    page_size: int = Field(description="Số items mỗi trang")
    total_pages: int = Field(description="Tổng số trang")
    has_next: bool = Field(description="Có trang tiếp theo không?")
    has_prev: bool = Field(description="Có trang trước không?")
    
    @classmethod
    def create(
        cls,
        items: list[DataType],
        total: int,
        page: int,
        page_size: int,
    ) -> "PagedResponse[DataType]":
        """Factory method để tạo PagedResponse dễ dàng hơn."""
        total_pages = max(1, -(-total // page_size))  # Ceiling division
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )


# ===================================
# Standard Response Wrappers
# ===================================
class SuccessResponse(BaseModel, Generic[DataType]):
    """
    Standard success response wrapper.
    
    Nhiều API chuẩn wrap response trong object có "data" field:
    {
        "success": true,
        "message": "User created successfully",
        "data": { ... }
    }
    """
    success: bool = True
    message: str = "Success"
    data: DataType | None = None


class ErrorDetail(BaseModel):
    """Chi tiết của một lỗi validation."""
    field: str | None = None
    message: str


class ErrorResponse(BaseModel):
    """
    Standard error response structure.
    
    Dùng nhất quán cho tất cả error responses.
    """
    success: bool = False
    message: str
    errors: list[ErrorDetail] | None = None
    error_code: str | None = None


# ===================================
# Auth Schemas  
# ===================================
class LoginRequest(BaseModel):
    """Request body cho POST /auth/login."""
    username: str  # Có thể là username hoặc email
    password: str


class TokenResponse(BaseModel):
    """Response sau khi login thành công."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Thời gian hết hạn (giây)")


class RefreshTokenRequest(BaseModel):
    """Request body cho POST /auth/refresh."""
    refresh_token: str

