"""
app/core/database.py
=====================
Cấu hình kết nối database sử dụng SQLAlchemy 2.0 Async.

KIẾN TRÚC DATABASE LAYER:
==========================
Engine → SessionFactory → Session → ORM Operations
  │           │              │
  │           │              └── Thực tế tương tác với DB
  │           └── Factory tạo Session mới cho mỗi request
  └── Kết nối vật lý đến DB (connection pool)

TẠI SAO DÙNG ASYNC?
===================
FastAPI là async framework. Nếu dùng sync database calls, 
bạn sẽ BLOCK event loop, làm chậm toàn bộ server.
Với async, trong khi chờ DB response, server vẫn xử lý được requests khác.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# ===================================
# 1. Base Class cho tất cả ORM Models
# ===================================
class Base(DeclarativeBase):
    """
    Base class cho tất cả SQLAlchemy models.
    
    Mọi model đều phải kế thừa từ class này.
    SQLAlchemy sẽ tự động:
    - Theo dõi tất cả models kế thừa Base
    - Tạo bảng khi gọi Base.metadata.create_all()
    - Quản lý relationships giữa các models
    """
    pass


# ===================================
# 2. Async Engine — Kết nối vật lý đến DB
# ===================================
_is_sqlite = "sqlite" in settings.DATABASE_URL

# SQLite và PostgreSQL có cấu hình engine khác nhau:
# - SQLite: Dùng StaticPool (1 kết nối dùng chung), không hỗ trợ pool_size/max_overflow
# - PostgreSQL: Dùng connection pool với nhiều kết nối song song
if _is_sqlite:
    # SQLite — chỉ dùng cho development/testing
    from sqlalchemy.pool import StaticPool
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,  # Dùng 1 connection duy nhất (phù hợp SQLite)
    )
else:
    # PostgreSQL / MySQL — dùng cho staging/production
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_size=10,        # Số kết nối tối đa trong pool
        max_overflow=20,     # Số kết nối thêm khi pool đầy
        pool_pre_ping=True,  # Kiểm tra kết nối còn sống trước khi dùng
        pool_recycle=3600,   # Tái sử dụng kết nối sau 1 giờ (tránh timeout)
    )


# ===================================
# 3. Session Factory — Tạo Session mới
# ===================================
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    
    # expire_on_commit=False: Giữ objects accessible sau khi commit
    # Quan trọng trong async context để tránh lazy loading issues
    expire_on_commit=False,
    
    autocommit=False,   # Phải gọi commit() thủ công
    autoflush=False,    # Phải gọi flush() thủ công (hoặc để session tự làm khi cần)
)


# ===================================
# 4. Database Dependency — Inject vào Route Handlers
# ===================================
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency cung cấp database session cho mỗi request.
    
    LUỒNG HOẠT ĐỘNG:
    ================
    1. Request đến → FastAPI gọi get_db()
    2. Session mới được tạo
    3. Session được inject vào route handler
    4. Route handler thực hiện operations
    5. Nếu thành công → session.commit() (nếu có changes)
    6. Dù thành công hay thất bại → session.close() (cleanup)
    
    DÙNG NHƯ THẾ NÀO:
    ==================
    @router.get("/users")
    async def get_users(db: AsyncSession = Depends(get_db)):
        # db đã được tạo và inject tự động
        result = await db.execute(select(User))
        ...
    
    GHI CHÚ: Đây là "per-request" session pattern.
    Mỗi HTTP request có 1 session riêng, tránh shared state giữa requests.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Nếu không có exception → commit changes
            await session.commit()
        except Exception:
            # Nếu có exception → rollback để đảm bảo data consistency
            await session.rollback()
            raise
        finally:
            # Luôn đóng session dù có exception hay không
            await session.close()


# ===================================
# 5. Helper Functions
# ===================================
async def create_all_tables() -> None:
    """
    Tạo tất cả tables trong database.
    
    Dùng trong development/testing.
    Trong production, dùng Alembic migrations thay vì hàm này!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_all_tables() -> None:
    """
    Xóa tất cả tables trong database.
    
    CHÚ Ý: CHỈ dùng trong testing! Không bao giờ dùng trong production!
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

