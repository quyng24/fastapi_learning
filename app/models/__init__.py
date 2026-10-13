"""
app/models/__init__.py
======================
Export all models so SQLAlchemy registry knows about them.
"""

from app.models.base import Base, BaseModel
from app.models.user import User
from app.models.post import Post, PostStatus

__all__ = ["Base", "BaseModel", "User", "Post", "PostStatus"]

