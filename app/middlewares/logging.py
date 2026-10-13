"""
app/middlewares/logging.py
===========================
Custom Logging Middleware — Log mọi request và response.

MIDDLEWARE TRONG FASTAPI:
==========================
Middleware bao bọc quanh tất cả requests/responses.
Giống như "interceptor" — chạy trước VÀ sau mỗi request.

USE CASES PHỔ BIẾN:
====================
- Logging: Log request/response time, status codes
- CORS: Add Cross-Origin headers  
- Authentication: Check auth token trước khi route handler chạy
- Rate Limiting: Giới hạn số requests từ một IP
- Request ID: Thêm unique ID vào mỗi request để trace logs

THỨ TỰ MIDDLEWARE:
==================
Middleware được thêm theo kiểu LIFO (Last In, First Out).
Middleware thêm sau sẽ chạy TRƯỚC đối với request,
và chạy SAU đối với response.

app.add_middleware(MiddlewareA)  # Chạy thứ 2 với request, thứ 1 với response
app.add_middleware(MiddlewareB)  # Chạy thứ 1 với request, thứ 2 với response
"""

import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Log thông tin mỗi request:
    - Method, URL, User-Agent
    - Response status code
    - Request processing time
    - Request ID (để trace logs)
    """
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        dispatch() chạy cho MỌI request.
        
        call_next: Hàm để chuyển request cho handler tiếp theo.
        Giống như `next()` trong Express.js middleware.
        """
        # === BEFORE REQUEST ===
        request_id = str(uuid.uuid4())[:8]  # Short unique ID
        start_time = time.perf_counter()
        
        # Thêm request_id vào request state để dùng trong handlers
        request.state.request_id = request_id
        
        # Log request
        print(
            f"[{request_id}] → {request.method} {request.url.path}"
            f" | Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # === CALL HANDLER ===
        response = await call_next(request)
        
        # === AFTER RESPONSE ===
        process_time = (time.perf_counter() - start_time) * 1000  # milliseconds
        
        # Thêm headers vào response
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.2f}ms"
        
        # Log response
        print(
            f"[{request_id}] ← {response.status_code}"
            f" | {process_time:.2f}ms"
        )
        
        return response

