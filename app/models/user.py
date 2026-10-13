"""
app/models/user.py
==================
SQLAlchemy ORM Model cho User.

QUAN TRỌNG — Phân biệt 3 loại "Model":
========================================
1. SQLAlchemy Model (file này): Ánh xạ trực tiếp với database table
   → Dùng để query, insert, update, delete
   
2. Pydantic Schema (app/schemas/): Validate và serialize data
   → Dùng cho request body và response body
   
3. Domain Model (tùy dự án): Business objects thuần Python
   → Chứa business rules, không phụ thuộc vào DB hay HTTP

NGUYÊN TẮC: ORM Model và Pydantic Schema là KHÁC NHAU và phục vụ mục đích khác nhau!
"""

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.post import Post


class User(BaseModel):
    """
    Database table: users
    
    BẢNG HỌC - Mapped vs Column:
    ==============================
    SQLAlchemy 2.0 dùng "mapped_column" với type annotations:
    
    Cũ (SQLAlchemy 1.x):
        name = Column(String(100), nullable=False)
    
    Mới (SQLAlchemy 2.0):
        name: Mapped[str] = mapped_column(String(100))
    
    Lợi ích của cách mới: type hints rõ ràng, IDE support tốt hơn.
    """
    
    __tablename__ = "users"
    
    # ===================================
    # Basic Fields
    # ===================================
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,         # Mỗi email chỉ xuất hiện 1 lần
        nullable=False,
        index=True,          # Tạo index để query theo email nhanh hơn
        comment="Email người dùng (unique)",
    )
    
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Tên đăng nhập (unique)",
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Password đã được hash (không lưu plain text!)",
    )
    
    full_name: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,       # Nullable → Không bắt buộc nhập
        comment="Tên đầy đủ của người dùng",
    )
    
    bio: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Tiểu sử ngắn",
    )
    
    # ===================================
    # Status Fields
    # ===================================
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Tài khoản có đang active không?",
    )
    
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email đã được xác thực chưa?",
    )
    
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Có phải admin/superuser không?",
    )
    
    # ===================================
    # Relationships
    # ===================================
    # BẢNG HỌC: Relationship cho phép truy cập data từ bảng liên quan
    # Ví dụ: user.posts → lấy tất cả posts của user này
    #
    # lazy="selectin": SQLAlchemy tự động load posts bằng SELECT WHERE IN query
    # Phù hợp cho async (không dùng lazy="subquery" với async!)
    posts: Mapped[list["Post"]] = relationship(
        "Post",
        back_populates="author",
        lazy="selectin",
        cascade="all, delete-orphan",  # Xóa user → xóa luôn posts
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"

