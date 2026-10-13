"""
app/main.py
============
Entry Point của ứng dụng FastAPI.

Đây là file đầu tiên được chạy khi khởi động server.
Nó "lắp ráp" tất cả components lại với nhau.

KHỞI ĐỘNG SERVER:
=================
uvicorn app.main:app --reload
  │       │    │    └── Tự reload khi code thay đổi (development only)
  │       │    └── Instance app trong file app/main.py
  │       └── Python module path: app/main.py
  └── Uvicorn: ASGI server

ASGI vs WSGI:
=============
- WSGI (Flask, Django cũ): Synchronous, không hỗ trợ async
- ASGI (FastAPI, Django 4+): Asynchronous, hỗ trợ async/await, WebSocket
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import create_all_tables
from app.exceptions.handlers import register_exception_handlers
from app.middlewares.logging import RequestLoggingMiddleware

# Import tất cả models để SQLAlchemy Base biết về các tables
from app.models import user, post  # noqa: F401


# ===================================
# Lifespan — Startup & Shutdown Events
# ===================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager — Chạy code khi start và shutdown.
    
    BẢNG HỌC: Đây là cách mới thay thế @app.on_event("startup").
    
    Cấu trúc:
    - Code TRƯỚC yield: Chạy khi startup (khởi tạo resources)
    - Code SAU yield: Chạy khi shutdown (cleanup resources)
    
    Ví dụ sử dụng:
    - Startup: Tạo tables, kết nối Redis, warm up caches
    - Shutdown: Đóng database connections, flush logs
    """
    # ===== STARTUP =====
    print("[START] Starting FastAPI application...")

    # Tạo database tables (chỉ trong development)
    # Production: Dùng alembic migrations thay vì create_all_tables()
    if settings.ENVIRONMENT == "development":
        await create_all_tables()
        print("[OK] Database tables created/verified")

    print(f"[INFO] App: {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"[INFO] Environment: {settings.ENVIRONMENT}")
    print(f"[INFO] Debug mode: {settings.DEBUG}")
    print("[OK] Application started successfully!")

    yield  # Server chay binh thuong o day

    # ===== SHUTDOWN =====
    print("[STOP] Shutting down application...")
    print("[OK] Application shut down cleanly")


# ===================================
# FastAPI App Instance
# ===================================
def create_app() -> FastAPI:
    """
    App Factory — Tạo FastAPI instance.
    
    BẢNG HỌC: App Factory Pattern cho phép:
    1. Tái sử dụng trong tests với config khác
    2. Code gọn gàng hơn (không phải đặt mọi thứ ở module level)
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="""
        ## FastAPI Backend Architecture Learning Project
        
        API được thiết kế theo **Layered Architecture**:
        - **Endpoints**: HTTP request/response handling
        - **Services**: Business logic  
        - **Repositories**: Database operations
        
        ### Authentication
        Dùng **Bearer Token** (JWT) cho các endpoints cần auth.
        """,
        docs_url="/docs" if settings.DEBUG else None,       # Swagger UI
        redoc_url="/redoc" if settings.DEBUG else None,     # ReDoc UI
        openapi_url="/openapi.json" if settings.DEBUG else None,
        lifespan=lifespan,
    )
    
    # ===================================
    # Middlewares (thứ tự quan trọng!)
    # ===================================
    # CORS — Phải đặt TRƯỚC các middleware khác
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Custom middlewares
    app.add_middleware(RequestLoggingMiddleware)
    
    # ===================================
    # Exception Handlers
    # ===================================
    register_exception_handlers(app)
    
    # ===================================
    # Routers
    # ===================================
    app.include_router(
        api_v1_router,
        prefix="/api/v1",
    )
    
    # Health check endpoint (không cần version prefix)
    @app.get("/health", tags=["Health"], include_in_schema=False)
    async def health_check():
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    
    return app


# ===================================
# App Instance (dùng bởi uvicorn)
# ===================================
app = create_app()


# ===================================
# Development Runner
# ===================================
if __name__ == "__main__":
    """
    Chạy trực tiếp: python app/main.py
    
    KHÔNG dùng cách này trong production.
    Production dùng: uvicorn app.main:app --workers 4
    """
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )

