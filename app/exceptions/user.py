"""
app/exceptions/user.py
=======================
Custom Domain Exceptions cho User.

TẠI SAO CẦN CUSTOM EXCEPTIONS?
================================
1. TÁCH BIỆT CONCERNS: Service layer không biết về HTTP.
   Service raise UserNotFoundError, không phải HTTPException(404).
   
2. DỄ TEST: Test service mà không cần HTTP context.

3. RÕ RÀNG HƠN: `raise UserNotFoundError(user_id)` rõ ràng hơn 
   `raise HTTPException(status_code=404, detail=f"User {user_id} not found")`

4. CENTRALIZED ERROR HANDLING: Exception handler ở một nơi,
   không rải rác HTTPException khắp nơi.

FLOW:
=====
Service → raise UserNotFoundError
      ↓
Exception Handler (app/exceptions/handlers.py)
      ↓
HTTPException(404) → Client
"""


class AppBaseException(Exception):
    """Base class cho tất cả custom exceptions trong ứng dụng."""
    
    def __init__(self, message: str, error_code: str | None = None):
        self.message = message
        self.error_code = error_code
        super().__init__(message)


# ===================================
# User Not Found
# ===================================
class UserNotFoundError(AppBaseException):
    """Raise khi không tìm thấy user."""
    
    def __init__(self, user_id: int | str):
        super().__init__(
            message=f"Không tìm thấy user với id={user_id}",
            error_code="USER_NOT_FOUND",
        )
        self.user_id = user_id


# ===================================
# Duplicate Errors
# ===================================
class EmailAlreadyExistsError(AppBaseException):
    """Raise khi email đã tồn tại."""
    
    def __init__(self, email: str):
        super().__init__(
            message=f"Email '{email}' đã được sử dụng",
            error_code="EMAIL_ALREADY_EXISTS",
        )
        self.email = email


class UsernameAlreadyExistsError(AppBaseException):
    """Raise khi username đã tồn tại."""
    
    def __init__(self, username: str):
        super().__init__(
            message=f"Username '{username}' đã được sử dụng",
            error_code="USERNAME_ALREADY_EXISTS",
        )
        self.username = username


# ===================================
# Auth Errors
# ===================================
class InvalidCredentialsError(AppBaseException):
    """Raise khi thông tin đăng nhập sai."""
    
    def __init__(self):
        super().__init__(
            message="Email/username hoặc password không đúng",
            error_code="INVALID_CREDENTIALS",
        )


class TokenExpiredError(AppBaseException):
    """Raise khi JWT token đã hết hạn."""
    
    def __init__(self):
        super().__init__(
            message="Token đã hết hạn, vui lòng đăng nhập lại",
            error_code="TOKEN_EXPIRED",
        )


class UnauthorizedError(AppBaseException):
    """Raise khi user không có quyền thực hiện action."""
    
    def __init__(self, action: str | None = None):
        message = "Bạn không có quyền thực hiện thao tác này"
        if action:
            message = f"Bạn không có quyền {action}"
        super().__init__(message=message, error_code="UNAUTHORIZED")


# ===================================
# Permission Errors
# ===================================
class ForbiddenError(AppBaseException):
    """Raise khi user đã authenticate nhưng không có permission."""
    
    def __init__(self, resource: str | None = None):
        message = "Truy cập bị từ chối"
        if resource:
            message = f"Bạn không có quyền truy cập {resource}"
        super().__init__(message=message, error_code="FORBIDDEN")

