"""
app/services/user.py
=====================
Service Layer — Business Logic cho User.

SERVICE LAYER LÀM GÌ?
======================
Service layer chứa BUSINESS LOGIC — các quy tắc nghiệp vụ của ứng dụng.

VÍ DỤ BUSINESS LOGIC:
- "Email phải unique" → Kiểm tra trước khi tạo user
- "Không thể xóa superuser cuối cùng" → Kiểm tra trước khi xóa
- "Khi tạo user, gửi email chào mừng" → Side effect sau khi tạo
- "Login sai 5 lần liên tiếp → khóa tài khoản 30 phút" → Complex logic

TÁCH BIỆT TRÁCH NHIỆM:
========================
Router/Endpoint  → Xử lý HTTP (parse request, trả response)
Service Layer    → Business logic (quy tắc nghiệp vụ)
Repository Layer → Database operations (SQL queries)

DEPENDENCY INJECTION:
=====================
Service nhận repository qua constructor (Dependency Injection).
Điều này giúp dễ test: trong test, inject mock repository thay vì real DB.
"""

from app.core.security import hash_password, verify_password
from app.exceptions.user import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    UserNotFoundError,
    UsernameAlreadyExistsError,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.common import LoginRequest, PagedResponse, PaginationParams
from app.schemas.user import UserCreate, UserResponse, UserUpdate


class UserService:
    """
    Service xử lý business logic liên quan đến User.
    
    Mọi business rule về User đều được đặt ở đây.
    Router chỉ gọi service methods, không biết gì về DB queries.
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Constructor injection — Repository được inject từ bên ngoài.
        
        Trong FastAPI, ta dùng Depends() để inject:
            def get_user_service(db: AsyncSession = Depends(get_db)):
                user_repo = UserRepository(db)
                return UserService(user_repo)
        """
        self.user_repo = user_repository
    
    # ===================================
    # Query Methods
    # ===================================
    async def get_user_by_id(self, user_id: int) -> User:
        """
        Lấy user theo ID.
        
        BẢNG HỌC: Service raise domain exception (UserNotFoundError),
        KHÔNG phải HTTPException. 
        HTTP exceptions được xử lý ở exception handler layer.
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundError(user_id)
        return user
    
    async def get_users_paginated(
        self,
        pagination: PaginationParams,
    ) -> PagedResponse[UserResponse]:
        """
        Lấy danh sách users với pagination.
        
        Returns PagedResponse với metadata về pagination.
        """
        users = await self.user_repo.get_active_users(
            skip=pagination.skip,
            limit=pagination.limit,
        )
        total = await self.user_repo.count(filters={"is_active": True})
        
        return PagedResponse.create(
            items=[UserResponse.model_validate(user) for user in users],
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
        )
    
    # ===================================
    # Create User
    # ===================================
    async def register_user(self, user_data: UserCreate) -> User:
        """
        Đăng ký tài khoản mới.
        
        Business Rules:
        1. Email phải chưa tồn tại trong hệ thống
        2. Username phải chưa tồn tại trong hệ thống
        3. Password phải được hash trước khi lưu
        4. (TODO) Gửi email xác thực sau khi tạo
        """
        # Rule 1: Kiểm tra email unique
        if await self.user_repo.email_exists(user_data.email):
            raise EmailAlreadyExistsError(user_data.email)
        
        # Rule 2: Kiểm tra username unique
        if await self.user_repo.username_exists(user_data.username):
            raise UsernameAlreadyExistsError(user_data.username)
        
        # Rule 3: Hash password
        hashed_password = hash_password(user_data.password)
        
        # Chuẩn bị data để lưu vào DB
        user_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "hashed_password": hashed_password,
            "full_name": user_data.full_name,
            "bio": user_data.bio,
        }
        
        # Tạo user trong DB
        new_user = await self.user_repo.create(user_dict)
        
        # Rule 4: TODO - Send welcome email
        # await self.email_service.send_welcome_email(new_user.email)
        
        return new_user
    
    # ===================================
    # Authentication
    # ===================================
    async def authenticate(self, credentials: LoginRequest) -> User:
        """
        Xác thực người dùng với username/email và password.
        
        Business Rules:
        1. Tìm user theo username hoặc email
        2. Kiểm tra user có active không
        3. Verify password
        
        SECURITY: Không tiết lộ chi tiết lỗi (ví dụ: "email không tồn tại" vs "sai password")
        → Luôn trả về "Invalid credentials" để tránh user enumeration attack.
        """
        # Tìm user
        user = await self.user_repo.get_by_email_or_username(credentials.username)
        
        if not user:
            raise InvalidCredentialsError()
        
        # Kiểm tra account active
        if not user.is_active:
            raise InvalidCredentialsError()
        
        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            raise InvalidCredentialsError()
        
        return user
    
    # ===================================
    # Update Methods
    # ===================================
    async def update_profile(self, user_id: int, update_data: UserUpdate) -> User:
        """
        Cập nhật thông tin profile user.
        
        Business Rules:
        - Chỉ update các fields được cung cấp (partial update)
        - User chỉ được update profile của chính mình (check ở dependency/endpoint)
        """
        user = await self.get_user_by_id(user_id)
        
        # Chỉ lấy fields có giá trị (exclude_none=True bỏ qua None values)
        update_dict = update_data.model_dump(exclude_none=True)
        
        if not update_dict:
            return user  # Không có gì để update
        
        return await self.user_repo.update(user, update_dict)
    
    async def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str,
    ) -> None:
        """
        Đổi password.
        
        Business Rules:
        1. Kiểm tra password hiện tại đúng không
        2. Hash password mới
        3. Lưu password mới
        """
        user = await self.get_user_by_id(user_id)
        
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError()
        
        # Hash và lưu password mới
        new_hashed = hash_password(new_password)
        await self.user_repo.update(user, {"hashed_password": new_hashed})
    
    # ===================================
    # Admin Methods
    # ===================================
    async def deactivate_user(self, user_id: int, admin_id: int) -> User:
        """
        Admin vô hiệu hóa tài khoản user.
        
        Business Rules:
        - Không thể tự vô hiệu hóa tài khoản của chính mình
        - Không thể vô hiệu hóa superuser khác
        """
        if user_id == admin_id:
            raise ValueError("Không thể vô hiệu hóa tài khoản của chính mình")
        
        user = await self.get_user_by_id(user_id)
        
        if user.is_superuser:
            raise ValueError("Không thể vô hiệu hóa tài khoản superuser")
        
        return await self.user_repo.deactivate_user(user)

