"""
app/repositories/base.py
=========================
Generic Base Repository — Repository Pattern.

REPOSITORY PATTERN LÀ GÌ?
===========================
Repository Pattern tạo ra một lớp abstraction giữa business logic và database.

KHÔNG CÓ Repository Pattern (BAD):
    class UserService:
        async def get_user(self, user_id: int, db: AsyncSession):
            # Business logic và DB query lẫn lộn
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            if not user:
                raise HTTPException(404, "User not found")
            return user

CÓ Repository Pattern (GOOD):
    class UserRepository:
        async def get_by_id(self, user_id: int) -> User | None:
            # Chỉ tập trung vào DB query
            result = await db.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()
    
    class UserService:
        def __init__(self, user_repo: UserRepository):
            self.user_repo = user_repo
        
        async def get_user(self, user_id: int) -> User:
            # Chỉ tập trung vào business logic
            user = await self.user_repo.get_by_id(user_id)
            if not user:
                raise UserNotFoundError(user_id)
            return user

LỢI ÍCH:
=========
1. Dễ test: Mock repository thay vì real database
2. Single Responsibility: Service không biết cách query database
3. DRY: Các query phổ biến viết 1 lần, dùng nhiều nơi
4. Swap database: Đổi từ PostgreSQL sang MongoDB chỉ cần rewrite repository
"""

from typing import Any, Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

# ModelType là placeholder cho bất kỳ SQLAlchemy model nào
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic repository với CRUD operations cơ bản.
    
    Generic[ModelType]: Cho phép tái sử dụng với bất kỳ model nào.
    
    Ví dụ:
        class UserRepository(BaseRepository[User]):
            pass
        
        class PostRepository(BaseRepository[Post]):
            pass
    
    Cả hai đều có sẵn: get_by_id(), create(), update(), delete(), get_all()
    """
    
    def __init__(self, model: type[ModelType], db: AsyncSession):
        """
        Args:
            model: SQLAlchemy model class (ví dụ: User, Post)
            db: Database session (inject từ FastAPI dependency)
        """
        self.model = model
        self.db = db
    
    # ===================================
    # READ Operations
    # ===================================
    async def get_by_id(self, record_id: int) -> ModelType | None:
        """
        Lấy một record theo primary key.
        
        Returns:
            Record nếu tìm thấy, None nếu không tìm thấy.
        """
        result = await self.db.execute(
            select(self.model).where(self.model.id == record_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        filters: dict[str, Any] | None = None,
    ) -> list[ModelType]:
        """
        Lấy danh sách records với pagination và filtering.
        
        Args:
            skip: Số records bỏ qua (dùng cho pagination)
            limit: Số records tối đa trả về
            filters: Dict các điều kiện filter {field_name: value}
        
        Ví dụ:
            # Lấy users active, trang 2
            users = await user_repo.get_all(
                skip=20, 
                limit=20, 
                filters={"is_active": True}
            )
        """
        query = select(self.model)
        
        # Áp dụng filters nếu có
        if filters:
            for field_name, value in filters.items():
                field = getattr(self.model, field_name, None)
                if field is not None and value is not None:
                    query = query.where(field == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def count(self, filters: dict[str, Any] | None = None) -> int:
        """
        Đếm tổng số records (dùng cho pagination).
        
        Args:
            filters: Dict các điều kiện filter
        
        Returns:
            Tổng số records thỏa mãn điều kiện
        """
        query = select(func.count()).select_from(self.model)
        
        if filters:
            for field_name, value in filters.items():
                field = getattr(self.model, field_name, None)
                if field is not None and value is not None:
                    query = query.where(field == value)
        
        result = await self.db.execute(query)
        return result.scalar_one()
    
    # ===================================
    # WRITE Operations
    # ===================================
    async def create(self, obj_data: dict[str, Any]) -> ModelType:
        """
        Tạo record mới trong database.
        
        Args:
            obj_data: Dict chứa data để tạo record
        
        Returns:
            Record vừa được tạo (với id đã được DB assign)
        
        Luồng:
        1. Tạo model instance với data
        2. add() → thêm vào session (chưa commit xuống DB)
        3. flush() → gửi SQL xuống DB nhưng chưa commit (để lấy id)
        4. refresh() → load lại data từ DB (đảm bảo data mới nhất)
        """
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.flush()    # Lấy generated id từ DB
        await self.db.refresh(db_obj)  # Load lại data
        return db_obj
    
    async def update(
        self,
        db_obj: ModelType,
        update_data: dict[str, Any],
    ) -> ModelType:
        """
        Cập nhật record đã có.
        
        Args:
            db_obj: SQLAlchemy object cần update (đã được load từ DB)
            update_data: Dict chứa fields cần cập nhật
        
        Returns:
            Record đã được cập nhật
        """
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj
    
    async def delete(self, db_obj: ModelType) -> None:
        """
        Xóa record khỏi database.
        
        Args:
            db_obj: SQLAlchemy object cần xóa
        """
        await self.db.delete(db_obj)
        await self.db.flush()
    
    async def soft_delete(self, db_obj: ModelType) -> ModelType:
        """
        Soft delete: Đánh dấu record là deleted thay vì xóa thật sự.
        
        BẢNG HỌC: Soft delete là pattern phổ biến trong production.
        Ưu điểm:
        - Có thể khôi phục data
        - Audit trail (biết ai xóa khi nào)
        - Không phá vỡ foreign key references
        
        Yêu cầu: Model phải có field `is_deleted` hoặc `deleted_at`.
        """
        if hasattr(db_obj, "is_deleted"):
            return await self.update(db_obj, {"is_deleted": True})
        raise NotImplementedError(f"{self.model.__name__} không hỗ trợ soft delete")

