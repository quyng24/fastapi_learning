# Module 03 — Repository Pattern & CRUD

## 🎯 Mục Tiêu Module Này

Hiểu sâu Repository Pattern, viết complex queries với SQLAlchemy 2.0.

---

## 📖 Lý Thuyết

### Repository Pattern — Tại sao quan trọng?

```
❌ KHÔNG có Repository:
Service layer chứa:
  - Business logic
  - SQL queries lẫn lộn
  - Khó test (cần real DB)
  - Khó maintain

✅ CÓ Repository:
Service layer chứa:     Repository layer chứa:
  - Business logic        - SQL queries
  - Gọi repo methods      - ORM operations
  - Dễ test (mock repo)   - DB-specific code
```

### SQLAlchemy 2.0 — Core Patterns

```python
# SELECT
result = await db.execute(select(User).where(User.is_active == True))
users = result.scalars().all()

# SELECT with JOIN
result = await db.execute(
    select(Post).join(User).where(User.username == "admin")
)

# INSERT
db.add(new_user)
await db.flush()  # Gửi SQL nhưng chưa commit

# UPDATE
user.email = "new@email.com"
await db.flush()

# DELETE
await db.delete(user)
```

---

## 📝 BÀI TẬP

### Bài 3.1 — Đọc và Phân Tích BaseRepository (30 phút)

Đọc [`app/repositories/base.py`](../../app/repositories/base.py):

1. `Generic[ModelType]` hoạt động như thế nào? Tại sao dùng TypeVar?
2. Tại sao dùng `flush()` thay vì `commit()` trong repository methods?
3. `expire_on_commit=False` trong session config có ý nghĩa gì?

---

### Bài 3.2 — Tạo PostRepository (2 giờ)

**Yêu cầu:** Tạo `app/repositories/post.py` với các methods:

```python
class PostRepository(BaseRepository[Post]):

    async def get_by_slug(self, slug: str) -> Post | None: ...

    async def get_published_posts(
        self,
        skip: int = 0,
        limit: int = 20,
        author_id: int | None = None,
    ) -> list[Post]: ...

    async def search_posts(
        self,
        query: str,
        skip: int = 0,
        limit: int = 20
    ) -> list[Post]:
        """
        Tìm kiếm bài viết theo title hoặc content.
        Hint: Dùng SQLAlchemy ilike() cho case-insensitive search.
        """
        ...

    async def increment_view_count(self, post_id: int) -> None:
        """
        Tăng view_count lên 1 (atomic operation).
        Hint: Dùng UPDATE posts SET view_count = view_count + 1
        Không dùng read-then-write (race condition!)
        """
        ...

    async def get_popular_posts(self, limit: int = 10) -> list[Post]:
        """Lấy bài viết có nhiều view nhất."""
        ...
```

---

### Bài 3.3 — Advanced Queries (2 giờ)

**Yêu cầu:** Thêm vào PostRepository:

1. **Filter by date range:**

```python
async def get_posts_in_date_range(
    self,
    start_date: datetime,
    end_date: datetime,
) -> list[Post]: ...
```

2. **Aggregate query:**

```python
async def get_author_stats(self, author_id: int) -> dict:
    """
    Trả về:
    {
        "total_posts": 10,
        "published_posts": 7,
        "total_views": 1250,
        "average_views": 178.5
    }

    Hint: Dùng func.count(), func.sum(), func.avg()
    """
    ...
```

3. **Bulk operations:**

```python
async def bulk_publish(self, post_ids: list[int]) -> int:
    """
    Publish nhiều posts cùng lúc.
    Returns: Số posts đã được publish.

    Hint: Dùng update() statement thay vì loop từng post (efficient hơn nhiều!)
    """
    ...
```

---

### Bài 3.4 — Unit of Work Pattern (nâng cao, 3 giờ)

**Vấn đề:** Khi một operation cần update nhiều tables, làm sao đảm bảo tất cả thành công hoặc tất cả rollback?

**Ví dụ:** Khi user đăng bài:

1. Tạo Post
2. Update user's post_count
3. Gửi notification

Nếu bước 2 fail → bước 1 phải rollback!

**Yêu cầu:** Implement Unit of Work pattern:

```python
class UnitOfWork:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.users = UserRepository(session)
        self.posts = PostRepository(session)

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

# Sử dụng:
async with UnitOfWork(db) as uow:
    post = await uow.posts.create(post_data)
    await uow.users.increment_post_count(author_id)
    # Nếu bất kỳ bước nào raise exception → tự động rollback
```

---

## ✅ Checklist

- [ ] Giải thích được lợi ích của Repository Pattern
- [ ] Tạo PostRepository với các queries cơ bản
- [ ] Implement search và aggregate queries
- [ ] Hiểu atomic operations (tránh race conditions)
- [ ] (Nâng cao) Implement Unit of Work pattern

---

➡️ **Tiếp theo:** [Module 04 — Service Layer & Business Logic](../module_04/README.md)
