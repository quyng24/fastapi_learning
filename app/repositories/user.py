"""
app/repositories/user.py
========================
Repository cho User model — Chứa tất cả database queries liên quan đến User.
"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository xử lý tất cả DB operations cho User.
    
    Kế thừa từ BaseRepository[User]:
    - Tự động có: get_by_id(), get_all(), count(), create(), update(), delete()
    - Thêm các methods đặc thù cho User: get_by_email(), get_by_username(), ...
    """
    
    def __init__(self, db: AsyncSession):
        # Truyền User model class vào BaseRepository
        super().__init__(model=User, db=db)
    
    # ===================================
    # Custom Query Methods
    # ===================================
    async def get_by_email(self, email: str) -> User | None:
        """
        Tìm user theo email.
        Dùng trong: login, check email trùng khi đăng ký.
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_username(self, username: str) -> User | None:
        """Tìm user theo username."""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()
    
    async def get_by_email_or_username(self, identifier: str) -> User | None:
        """
        Tìm user theo email HOẶC username.
        Dùng cho login flow (user có thể login bằng email hoặc username).
        
        BẢNG HỌC: SQLAlchemy OR condition
        """
        result = await self.db.execute(
            select(User).where(
                or_(
                    User.email == identifier,
                    User.username == identifier,
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def email_exists(self, email: str) -> bool:
        """Kiểm tra email đã tồn tại trong DB chưa."""
        user = await self.get_by_email(email)
        return user is not None
    
    async def username_exists(self, username: str) -> bool:
        """Kiểm tra username đã tồn tại trong DB chưa."""
        user = await self.get_by_username(username)
        return user is not None
    
    async def get_active_users(self, skip: int = 0, limit: int = 20) -> list[User]:
        """Lấy danh sách users đang active."""
        return await self.get_all(
            skip=skip,
            limit=limit,
            filters={"is_active": True},
        )
    
    async def verify_user(self, user: User) -> User:
        """Đánh dấu user đã xác thực email."""
        return await self.update(user, {"is_verified": True})
    
    async def deactivate_user(self, user: User) -> User:
        """Vô hiệu hóa tài khoản user."""
        return await self.update(user, {"is_active": False})

