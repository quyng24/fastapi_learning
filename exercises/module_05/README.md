# Module 05 — Authentication, Dependencies & Middleware

## 🎯 Mục Tiêu Module Này

Hiểu sâu FastAPI Dependency Injection, implement JWT auth flow hoàn chỉnh, tạo custom middleware.

---

## 📖 Lý Thuyết

### FastAPI Dependency Injection

```
Dependency Injection (DI) là pattern:
"Thay vì tự tạo dependencies, nhận chúng từ bên ngoài"

Không có DI:
class UserService:
    def __init__(self):
        self.db = create_db_connection()  # Tự tạo → khó test!
        self.repo = UserRepository(self.db)

Có DI:
class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo  # Nhận từ bên ngoài → dễ test!

FastAPI's Depends() tự động resolve dependencies:
@router.get("/users")
async def list_users(
    db: AsyncSession = Depends(get_db),           # DI: DB session
    current_user: User = Depends(get_current_user), # DI: Auth user
    service: UserService = Depends(get_user_service) # DI: Service
):
    ...
```

### JWT Token Flow

```
┌──────┐  POST /auth/login   ┌──────────┐
│Client│ ──────────────────→ │  Server  │
│      │  {username, pass}   │          │
│      │                     │ Verify   │
│      │   {access_token,    │ credentials
│      │ ←─ refresh_token}   │ Create JWT│
│      │                     └──────────┘
│      │
│      │  GET /api/users     ┌──────────┐
│      │ ──────────────────→ │  Server  │
│      │  Authorization:     │          │
│      │  Bearer <token>     │ Decode   │
│      │                     │ JWT      │
│      │   Response data     │ Query DB │
│      │ ←────────────────── │ for user │
└──────┘                     └──────────┘
```

---

## 📝 BÀI TẬP

### Bài 5.1 — Phân tích Dependencies (30 phút)

Đọc [`app/dependencies/auth.py`](../../app/dependencies/auth.py):

1. Vẽ sơ đồ dependency chain từ `get_current_superuser` → `get_current_active_user` → `get_current_user` → `get_db`
2. `dependencies=[Depends(get_current_superuser)]` trong router khác gì `current_user: User = Depends(get_current_superuser)` trong function signature?
3. `get_optional_current_user` dùng trong trường hợp nào?

---

### Bài 5.2 — Permission-based Authorization (2 giờ)

**Yêu cầu:** Implement role-based access control (RBAC):

```python
# app/dependencies/permissions.py
from enum import Enum

class Permission(str, Enum):
    USER_READ = "user:read"
    USER_WRITE = "user:write"
    POST_READ = "post:read"
    POST_WRITE = "post:write"
    POST_DELETE = "post:delete"
    ADMIN = "admin"

def require_permission(permission: Permission):
    """
    Factory function tạo dependency kiểm tra permission.

    Dùng:
    @router.delete("/posts/{id}")
    async def delete_post(
        post_id: int,
        _: None = Depends(require_permission(Permission.POST_DELETE))
    ):
        ...
    """
    async def check_permission(
        current_user: User = Depends(get_current_active_user)
    ) -> None:
        # Implement permission check
        ...

    return check_permission

# Dùng:
@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    _=Depends(require_permission(Permission.POST_DELETE)),
    service=Depends(get_post_service),
):
    ...
```

---

### Bài 5.3 — Resource Ownership Check (2 giờ)

**Business Rule:** User chỉ có thể edit/delete posts của chính mình (trừ admin).

**Yêu cầu:** Implement dependency:

```python
def get_post_if_owner(
    post_id: int,
    current_user: User = Depends(get_current_active_user),
    service: PostService = Depends(get_post_service),
) -> Post:
    """
    Lấy post và verify current_user là owner (hoặc admin).

    Raises ForbiddenError nếu không phải owner.
    """
    post = await service.get_post_by_id(post_id)

    if post.author_id != current_user.id and not current_user.is_superuser:
        raise ForbiddenError(f"Bạn không phải chủ của bài viết này")

    return post

# Dùng trong router:
@router.put("/{post_id}")
async def update_post(
    update_data: PostUpdate,
    post: Post = Depends(get_post_if_owner),  # Tự động check ownership!
    service=Depends(get_post_service),
):
    ...
```

---

### Bài 5.4 — Rate Limiting Middleware (3 giờ)

**Yêu cầu:** Tạo `app/middlewares/rate_limit.py` giới hạn requests:

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Giới hạn: 100 requests / phút / IP

    Implement với in-memory dictionary (development):
    {
        "127.0.0.1": {
            "count": 5,
            "window_start": datetime
        }
    }

    Production: Dùng Redis để share state giữa nhiều server instances.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        ...

    async def dispatch(self, request: Request, call_next) -> Response:
        client_ip = request.client.host

        # Kiểm tra rate limit
        if self.is_rate_limited(client_ip):
            return JSONResponse(
                status_code=429,
                content={"message": "Too many requests. Please try again later."},
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(self.max_requests),
                }
            )

        self.increment(client_ip)
        return await call_next(request)
```

---

### Bài 5.5 — Token Blacklist với Redis (3 giờ, nâng cao)

**Vấn đề:** JWT là stateless → không thể invalidate token sau khi issue.

**Giải pháp:** Lưu "blacklisted" tokens vào Redis.

**Yêu cầu:**

1. Khi user logout → add token vào Redis blacklist với TTL = thời gian còn lại của token
2. Trong `get_current_user` dependency → check token có trong blacklist không

```python
# app/core/token_blacklist.py
import redis.asyncio as redis

class TokenBlacklist:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def add_to_blacklist(self, token: str, expires_in: int) -> None:
        """Thêm token vào blacklist với TTL."""
        await self.redis.setex(
            f"blacklist:{token}",
            expires_in,
            "1"
        )

    async def is_blacklisted(self, token: str) -> bool:
        """Kiểm tra token có trong blacklist không."""
        return await self.redis.exists(f"blacklist:{token}") > 0
```

---

## ✅ Checklist

- [ ] Giải thích được Dependency Injection chain trong FastAPI
- [ ] Implement permission-based authorization với factory pattern
- [ ] Implement resource ownership check
- [ ] Tạo Rate Limiting middleware
- [ ] (Nâng cao) Implement Token Blacklist với Redis

---

➡️ **Tiếp theo:** [Module 06 — Testing, Error Handling & Production](../module_06/README.md)
