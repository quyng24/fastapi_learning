"""
app/core/security.py
=====================
Xử lý Authentication & Authorization.

KHÁI NIỆM:
===========
- Authentication (AuthN): Xác thực "Bạn là ai?" → Kiểm tra username/password
- Authorization (AuthZ): Phân quyền "Bạn được làm gì?" → Kiểm tra roles/permissions

JWT FLOW:
=========
1. User login → Server tạo JWT token → Trả về cho client
2. Client gửi token trong header: Authorization: Bearer <token>
3. Server verify token → Lấy user info từ token payload
4. Server kiểm tra user có quyền thực hiện action không

TẠI SAO DÙNG JWT?
=================
- Stateless: Server không cần lưu session → Scale horizontally dễ dàng
- Self-contained: Token chứa user info → Không cần query DB mỗi request
- Signed: Token được ký → Client không thể giả mạo
"""

from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# ===================================
# Password Hashing
# ===================================
def hash_password(password: str) -> str:
    """
    Hash password trước khi lưu vào database.
    
    QUAN TRỌNG: Không bao giờ lưu password dạng plain text!
    
    bcrypt tự động thêm "salt" vào mỗi password,
    nên cùng 1 password sẽ cho ra hash khác nhau mỗi lần.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes[:72], salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Kiểm tra password nhập vào có khớp với hash trong database không.
    
    Args:
        plain_password: Password người dùng nhập
        hashed_password: Hash lưu trong database
    
    Returns:
        True nếu password đúng, False nếu sai
    """
    try:
        pwd_bytes = plain_password.encode("utf-8")
        return bcrypt.checkpw(pwd_bytes[:72], hashed_password.encode("utf-8"))
    except Exception:
        return False


# ===================================
# JWT Token Creation & Verification
# ===================================
def create_access_token(
    subject: str | Any,
    expires_delta: timedelta | None = None,
    additional_claims: dict | None = None,
) -> str:
    """
    Tạo JWT Access Token.
    
    Args:
        subject: Thường là user ID hoặc username (định danh user)
        expires_delta: Thời gian token hết hạn (mặc định từ settings)
        additional_claims: Thêm data vào payload (ví dụ: roles, permissions)
    
    Returns:
        JWT token string
    
    JWT PAYLOAD STRUCTURE:
    ======================
    {
        "sub": "user_123",        # Subject (user identifier)
        "exp": 1234567890,        # Expiration time (Unix timestamp)
        "iat": 1234567000,        # Issued at time
        "type": "access",         # Token type
        ...additional_claims      # Custom data
    }
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.now(UTC) + expires_delta
    
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }
    
    if additional_claims:
        payload.update(additional_claims)
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str | Any) -> str:
    """
    Tạo JWT Refresh Token (có thời hạn dài hơn Access Token).
    
    Refresh Token dùng để lấy Access Token mới khi Access Token hết hạn,
    mà không cần user login lại.
    
    Thời hạn thường: 7-30 ngày.
    """
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expire = datetime.now(UTC) + expires_delta
    
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "refresh",
    }
    
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """
    Giải mã và verify JWT token.
    
    Raises:
        JWTError: Nếu token invalid, expired, hoặc signature không khớp
    
    Returns:
        Token payload (dictionary chứa user info)
    """
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


def verify_token(token: str, token_type: str = "access") -> dict[str, Any] | None:
    """
    Verify token và trả về payload nếu hợp lệ.
    
    Args:
        token: JWT token string
        token_type: Loại token cần verify ("access" hoặc "refresh")
    
    Returns:
        Token payload nếu hợp lệ, None nếu không hợp lệ
    """
    try:
        payload = decode_token(token)
        
        # Kiểm tra đúng loại token
        if payload.get("type") != token_type:
            return None
        
        return payload
    
    except JWTError:
        return None

