"""
app/exceptions/handlers.py
===========================
Global Exception Handlers — Chuyển đổi Domain Exceptions thành HTTP Responses.

LUỒNG XỬ LÝ:
=============
1. Service raise UserNotFoundError (domain exception)
2. FastAPI bắt exception
3. Handler tương ứng được gọi
4. Handler trả về JSONResponse với HTTP status code phù hợp

ĐĂNG KÝ TRONG main.py:
=======================
app.add_exception_handler(UserNotFoundError, user_not_found_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.user import (
    AppBaseException,
    EmailAlreadyExistsError,
    ForbiddenError,
    InvalidCredentialsError,
    TokenExpiredError,
    UnauthorizedError,
    UsernameAlreadyExistsError,
    UserNotFoundError,
)
from app.schemas.common import ErrorDetail, ErrorResponse


# ===================================
# Domain Exception Handlers
# ===================================
async def user_not_found_handler(
    request: Request,
    exc: UserNotFoundError,
) -> JSONResponse:
    """Handler cho UserNotFoundError → HTTP 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
        ).model_dump(),
    )


async def email_exists_handler(
    request: Request,
    exc: EmailAlreadyExistsError,
) -> JSONResponse:
    """Handler cho EmailAlreadyExistsError → HTTP 409 Conflict."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
            errors=[ErrorDetail(field="email", message=exc.message)],
        ).model_dump(),
    )


async def username_exists_handler(
    request: Request,
    exc: UsernameAlreadyExistsError,
) -> JSONResponse:
    """Handler cho UsernameAlreadyExistsError → HTTP 409 Conflict."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content=ErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
            errors=[ErrorDetail(field="username", message=exc.message)],
        ).model_dump(),
    )


async def invalid_credentials_handler(
    request: Request,
    exc: InvalidCredentialsError,
) -> JSONResponse:
    """Handler cho InvalidCredentialsError → HTTP 401 Unauthorized."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
        ).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def unauthorized_handler(
    request: Request,
    exc: UnauthorizedError,
) -> JSONResponse:
    """Handler cho UnauthorizedError → HTTP 401."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
        ).model_dump(),
        headers={"WWW-Authenticate": "Bearer"},
    )


async def forbidden_handler(
    request: Request,
    exc: ForbiddenError,
) -> JSONResponse:
    """Handler cho ForbiddenError → HTTP 403."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=ErrorResponse(
            message=exc.message,
            error_code=exc.error_code,
        ).model_dump(),
    )


# ===================================
# Pydantic Validation Error Handler
# ===================================
async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handler cho Pydantic validation errors → HTTP 422.
    
    Mặc định FastAPI trả về format khá khó đọc.
    Handler này format lại cho dễ đọc hơn.
    """
    errors = []
    for error in exc.errors():
        field = " → ".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append(
            ErrorDetail(
                field=field or None,
                message=error["msg"],
            )
        )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            message="Dữ liệu đầu vào không hợp lệ",
            error_code="VALIDATION_ERROR",
            errors=errors,
        ).model_dump(),
    )


# ===================================
# Catch-all Handler
# ===================================
async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Handler cuối cùng cho bất kỳ exception nào chưa được xử lý.
    
    QUAN TRỌNG: Không expose chi tiết lỗi cho client trong production!
    Log lỗi ở server, trả về message chung chung cho client.
    """
    # TODO: Log exception với proper logging
    # logger.error(f"Unhandled exception: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            message="Đã xảy ra lỗi hệ thống. Vui lòng thử lại sau.",
            error_code="INTERNAL_SERVER_ERROR",
        ).model_dump(),
    )


def register_exception_handlers(app) -> None:
    """
    Đăng ký tất cả exception handlers với FastAPI app.
    
    Gọi hàm này trong main.py:
        register_exception_handlers(app)
    """
    from fastapi.exceptions import RequestValidationError
    
    app.add_exception_handler(UserNotFoundError, user_not_found_handler)
    app.add_exception_handler(EmailAlreadyExistsError, email_exists_handler)
    app.add_exception_handler(UsernameAlreadyExistsError, username_exists_handler)
    app.add_exception_handler(InvalidCredentialsError, invalid_credentials_handler)
    app.add_exception_handler(UnauthorizedError, unauthorized_handler)
    app.add_exception_handler(ForbiddenError, forbidden_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

