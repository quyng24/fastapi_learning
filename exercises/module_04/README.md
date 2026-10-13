# Module 04 — Service Layer & Business Logic

## 🎯 Mục Tiêu Module Này

Viết Service layer đúng chuẩn, xử lý business logic phức tạp, tránh các anti-patterns phổ biến.

---

## 📖 Lý Thuyết

### Service Layer Rules

```
✅ Service NÊN:
- Chứa business rules
- Validate nghiệp vụ (không chỉ data validation)
- Orchestrate nhiều repositories
- Raise domain exceptions
- Xử lý side effects (gửi email, notifications)

❌ Service KHÔNG NÊN:
- Biết về HTTP (không dùng HTTPException, Request, Response)
- Trực tiếp query database (đó là việc của repository)
- Biết về cách serialize data (đó là việc của schema)
```

### Anemic Domain Model vs Rich Domain Model

```python
# ❌ ANEMIC - Logic nằm trong service, model chỉ là data container
class User:
    is_active: bool
    login_attempts: int

class UserService:
    def lock_account(self, user):
        if user.login_attempts >= 5:
            user.is_active = False
            user.locked_until = datetime.now() + timedelta(minutes=30)

# ✅ RICH DOMAIN - Logic nằm trong model (cho simple rules)
class User:
    is_active: bool
    login_attempts: int

    def lock_account(self):
        """User biết cách tự khóa account"""
        self.is_active = False
        self.locked_until = datetime.now() + timedelta(minutes=30)

    @property
    def should_lock(self) -> bool:
        return self.login_attempts >= 5
```

---

## 📝 BÀI TẬP

### Bài 4.1 — Đọc UserService (30 phút)

Đọc [`app/services/user.py`](../../app/services/user.py):

1. Tại sao `register_user()` raise `EmailAlreadyExistsError` thay vì `HTTPException(409)`?
2. `authenticate()` không tiết lộ lý do fail cụ thể — tại sao? (Hint: user enumeration attack)
3. `update_profile()` dùng `model_dump(exclude_none=True)` — điều đó nghĩa là gì?

---

### Bài 4.2 — Tạo PostService (3 giờ)

**Yêu cầu:** Tạo `app/services/post.py`:

```python
class PostService:

    async def create_post(
        self,
        post_data: PostCreate,
        author_id: int
    ) -> Post:
        """
        Business Rules:
        1. Tự động generate slug từ title
        2. Nếu slug đã tồn tại → thêm số vào cuối (bai-viet, bai-viet-1, bai-viet-2)
        3. Author phải là verified user
        """
        ...

    async def publish_post(self, post_id: int, author_id: int) -> Post:
        """
        Business Rules:
        1. Chỉ author hoặc admin mới có thể publish
        2. Post phải có title và content (không empty)
        3. Đổi status từ DRAFT → PUBLISHED
        """
        ...

    async def get_post_with_view_tracking(
        self,
        slug: str,
        viewer_id: int | None = None
    ) -> Post:
        """
        Business Rules:
        1. Lấy post theo slug
        2. Tăng view count (nhưng không tính view của chính author)
        3. Chỉ trả về PUBLISHED posts (trừ khi viewer là author/admin)
        """
        ...
```

---

### Bài 4.3 — Business Rules phức tạp (3 giờ)

**Scenario:** Implement Rate Limiting cho việc đăng bài.

**Business Rule:** "Mỗi user chỉ được đăng tối đa 5 bài trong 24 giờ"

```python
async def check_post_rate_limit(self, author_id: int) -> None:
    """
    Kiểm tra user có vượt quá giới hạn đăng bài không.

    Raises PostRateLimitExceededError nếu vượt quá giới hạn.

    Implementation:
    1. Đếm số posts user đã tạo trong 24 giờ qua
    2. Nếu >= MAX_POSTS_PER_DAY → raise exception

    Hint: Cần thêm query trong PostRepository:
    async def count_posts_in_last_hours(author_id, hours=24) -> int
    """
    ...
```

---

### Bài 4.4 — Event-Driven Side Effects (2 giờ, nâng cao)

**Concept:** Khi business event xảy ra, trigger các side effects.

**Ví dụ:** Khi user đăng bài mới:

- Gửi email notification cho followers
- Update user's statistics
- Index bài viết cho search

**Yêu cầu:** Implement simple event system:

```python
# app/events/post_events.py
from dataclasses import dataclass
from typing import Callable, Awaitable

@dataclass
class PostPublishedEvent:
    post_id: int
    author_id: int
    title: str

class EventBus:
    _handlers: dict[type, list[Callable]] = {}

    def subscribe(self, event_type: type, handler: Callable):
        ...

    async def publish(self, event):
        ...

# Trong PostService:
async def publish_post(self, ...):
    post = await self.post_repo.update(post, {"status": "published"})

    # Publish event → các handlers tự xử lý side effects
    await self.event_bus.publish(PostPublishedEvent(
        post_id=post.id,
        author_id=post.author_id,
        title=post.title,
    ))

    return post
```

---

## ✅ Checklist

- [ ] Giải thích được Service Layer responsibilities
- [ ] Tạo PostService với business rules
- [ ] Implement rate limiting logic
- [ ] Hiểu tại sao service raise domain exceptions (không phải HTTP exceptions)
- [ ] (Nâng cao) Implement event-driven side effects

---

➡️ **Tiếp theo:** [Module 05 — Authentication, Dependencies & Middleware](../module_05/README.md)
