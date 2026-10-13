"""
app/models/base.py
==================
Base model với các trường dùng chung.

THIẾT KẾ:
==========
Thay vì lặp lại id, created_at, updated_at trong mỗi model,
ta tạo một Base model chung để tái sử dụng (DRY principle).
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TimestampMixin:
    """
    Mixin thêm created_at và updated_at vào model.
    
    CÁCH DÙNG:
    ==========
    class User(Base, TimestampMixin):
        __tablename__ = "users"
        ...
    
    SQLAlchemy Mapped Column với type annotation:
    - Mapped[datetime] → Column không nullable
    - Mapped[datetime | None] → Column nullable
    """
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
        comment="Thời điểm tạo record",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),  # Tự cập nhật khi record thay đổi
        nullable=False,
        comment="Thời điểm cập nhật gần nhất",
    )


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model với id, created_at, updated_at.
    
    __abstract__ = True: SQLAlchemy sẽ không tạo bảng cho class này.
    Chỉ những class kế thừa nó mới có bảng thực sự.
    """
    __abstract__ = True
    
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        comment="Primary key tự tăng",
    )

