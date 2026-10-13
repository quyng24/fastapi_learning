"""
app/schemas/user.py
====================
Pydantic Schemas cho User.

PHÂN BIỆT SCHEMA vs MODEL:
============================
- SQLAlchemy Model: Ánh xạ với database table (app/models/user.py)
- Pydantic Schema: Validate HTTP request/response data (file này)

TẠI SAO CẦN TÁCH BIỆT?
========================
1. Security: Có thể ẩn fields nhạy cảm (hashed_password) khỏi response
2. Flexibility: Request có thể có shape khác response
3. Validation: Pydantic thêm validation rules không liên quan đến DB
4. Documentation: FastAPI tự động generate Swagger UI từ Schemas

PATTERN ĐẶT TÊN CHUẨN:
========================
UserCreate  → Schema cho POST request (tạo mới)
UserUpdate  → Schema cho PUT/PATCH request (cập nhật)
UserResponse → Schema cho response (trả về cho client)
UserInDB   → Schema với data từ DB (bao gồm cả hashed_password)
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


# ===================================
# Base Schema (shared fields)
# ===================================
class UserBase(BaseModel):
    """Fields chung giữa các schemas."""
    email: EmailStr
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",  # Chỉ cho phép chữ, số, _, -
        description="Tên đăng nhập (chỉ chứa chữ cái, số, _ và -)",
    )
    full_name: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=500)


# ===================================
# Create Schema (Request body khi tạo user)
# ===================================
class UserCreate(UserBase):
    """
    Schema cho POST /users endpoint.
    
    Thêm password field (chỉ có khi tạo mới, không trả về trong response).
    """
    password: str = Field(
        min_length=8,
        max_length=100,
        description="Password tối thiểu 8 ký tự",
    )
    password_confirm: str = Field(description="Nhập lại password để xác nhận")
    
    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Kiểm tra độ mạnh của password.
        
        BẢNG HỌC: field_validator chạy khi field đó được validate.
        Nếu raise ValueError, Pydantic sẽ trả về lỗi validation 422.
        """
        if not any(c.isupper() for c in v):
            raise ValueError("Password phải có ít nhất 1 chữ hoa")
        if not any(c.islower() for c in v):
            raise ValueError("Password phải có ít nhất 1 chữ thường")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password phải có ít nhất 1 chữ số")
        return v
    
    @field_validator("password_confirm")
    @classmethod
    def validate_passwords_match(cls, v: str, info) -> str:
        """Kiểm tra password_confirm khớp với password."""
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("Hai password không khớp nhau")
        return v


# ===================================
# Update Schema (Request body khi cập nhật)
# ===================================
class UserUpdate(BaseModel):
    """
    Schema cho PATCH /users/{id} endpoint.
    
    TẤT CẢ fields đều Optional → Client chỉ gửi fields muốn thay đổi.
    Đây là "Partial Update" pattern (HTTP PATCH).
    """
    full_name: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=500)
    # Chú ý: email và username thường không cho phép đổi sau khi tạo
    # Hoặc cần process riêng (verify email mới, kiểm tra username unique)


class UserUpdatePassword(BaseModel):
    """Schema riêng cho việc đổi password."""
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)
    new_password_confirm: str


# ===================================
# Response Schema (Trả về cho client)
# ===================================
class UserResponse(UserBase):
    """
    Schema cho response khi trả user data về client.
    
    LƯU Ý:
    - Không có password field (bảo mật!)
    - Thêm id, is_active, created_at (data từ DB)
    
    model_config với from_attributes=True:
    Cho phép Pydantic đọc data từ SQLAlchemy model object
    (thay vì chỉ từ dict).
    """
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}  # Quan trọng! Cho phép dùng với SQLAlchemy objects


class UserPublicResponse(BaseModel):
    """
    Schema cho public profile (khi xem profile của user khác).
    Chỉ expose thông tin không nhạy cảm.
    """
    id: int
    username: str
    full_name: str | None = None
    bio: str | None = None
    
    model_config = {"from_attributes": True}

