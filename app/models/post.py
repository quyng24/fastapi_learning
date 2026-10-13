"""
app/models/post.py
==================
SQLAlchemy ORM Model cho Post (bài viết).

Dùng để minh họa:
- Foreign Key relationship
- Many-to-One (Post → User)
- Enum field
"""

import enum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class PostStatus(str, enum.Enum):
    """
    Enum cho trạng thái bài viết.
    
    BẢNG HỌC: str + enum.Enum → Enum lưu dạng string trong DB (dễ đọc hơn integer).
    Ví dụ: PostStatus.PUBLISHED → lưu "published" trong DB.
    """
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class Post(BaseModel):
    """
    Database table: posts
    
    Relationship: Many Posts → One User (author)
    """
    
    __tablename__ = "posts"
    
    # ===================================
    # Content Fields
    # ===================================
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Tiêu đề bài viết",
    )
    
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Nội dung bài viết",
    )
    
    slug: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        nullable=False,
        comment="URL-friendly version của title (ví dụ: 'bai-viet-hay')",
    )
    
    status: Mapped[PostStatus] = mapped_column(
        default=PostStatus.DRAFT,
        nullable=False,
        comment="Trạng thái bài viết",
    )
    
    view_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
        comment="Số lượt xem",
    )
    
    # ===================================
    # Foreign Key
    # ===================================
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="ID của tác giả (foreign key đến bảng users)",
    )
    
    # ===================================
    # Relationships
    # ===================================
    author: Mapped["User"] = relationship(
        "User",
        back_populates="posts",
        lazy="selectin",
    )
    
    def __repr__(self) -> str:
        return f"<Post(id={self.id}, title='{self.title[:30]}...', status={self.status})>"

