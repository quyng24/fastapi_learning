# Module 02 — Models, Schemas & Database Layer

## 🎯 Mục Tiêu Module Này

Phân biệt rõ **SQLAlchemy Model** vs **Pydantic Schema**, hiểu cách thiết kế database layer.

---

## 📖 Lý Thuyết Quan Trọng

### Bộ Ba: Model → Schema → Response

```
Database Table          SQLAlchemy Model         Pydantic Schema
─────────────          ────────────────         ───────────────
users                  User(BaseModel)           UserResponse
  id INT PK    ──→       id: int        ──→       id: int
  email TEXT             email: str               email: str
  password TEXT          hashed_password: str     ← KHÔNG có (ẩn đi!)
  created_at             created_at: datetime     created_at: datetime
```

### Tại sao cần cả hai?

|                  | SQLAlchemy Model | Pydantic Schema    |
| ---------------- | ---------------- | ------------------ |
| Mục đích         | Map với DB table | Validate HTTP data |
| Nơi dùng         | Repository layer | Endpoint layer     |
| Có thể ẩn field? | Không            | ✅ Có              |
| Validation       | DB constraints   | Python validators  |

---

## 📝 BÀI TẬP

### Bài 2.1 — Phân tích Models (30 phút)

Đọc [`app/models/user.py`](../../app/models/user.py) và [`app/models/post.py`](../../app/models/post.py) và trả lời:

1. `Mapped[str]` khác `Mapped[str | None]` như thế nào? Điều đó ảnh hưởng gì đến database?
2. `index=True` trên `email` và `username` dùng để làm gì? Khi nào nên thêm index?
3. Relationship `posts` trong User với `lazy="selectin"` hoạt động như thế nào?
4. `cascade="all, delete-orphan"` có nghĩa là gì?

---

### Bài 2.2 — Tạo Model mới: `Comment` (2 giờ)

**Yêu cầu:** Tạo model `Comment` trong `app/models/comment.py`:

- Comment thuộc về 1 Post (Many Comments → One Post)
- Comment thuộc về 1 User (author)
- Comment có thể có parent comment (nested comments)
- Fields: `content`, `is_deleted` (soft delete), `author_id`, `post_id`, `parent_id`

**Gợi ý cấu trúc:**

```python
class Comment(BaseModel):
    __tablename__ = "comments"

    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(default=False)

    # Foreign Keys
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("comments.id"), nullable=True)

    # Relationships
    ...
```

---

### Bài 2.3 — Tạo Schemas cho Post (2 giờ)

**Yêu cầu:** Tạo file `app/schemas/post.py` với các schemas:

1. `PostCreate` — Request body khi tạo post (title, content)
2. `PostUpdate` — Request body khi update (tất cả optional)
3. `PostResponse` — Response trả về (include author info)
4. `PostListResponse` — Response cho list (không include full content, chỉ excerpt)

**Challenge:** Trong `PostResponse`, làm sao để include `author` (UserPublicResponse)?

```python
class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    author: UserPublicResponse  # Nested schema!
    status: PostStatus
    created_at: datetime

    model_config = {"from_attributes": True}
```

---

### Bài 2.4 — Slug Generation (1 giờ)

**Yêu cầu:** Tạo utility function `app/utils/slug.py`:

```python
def generate_slug(title: str) -> str:
    """
    Convert title thành URL-friendly slug.

    Ví dụ:
    "Bài Viết Hay Nhất 2024!" → "bai-viet-hay-nhat-2024"
    "Hello World" → "hello-world"
    """
    ...
```

**Hint:** Dùng thư viện `python-slugify` hoặc viết tay với `unicodedata.normalize`.

---

### Bài 2.5 — Database Migration với Alembic (2 giờ)

**Yêu cầu:** Setup Alembic và tạo migration đầu tiên.

```bash
# Khởi tạo Alembic (chỉ làm 1 lần)
alembic init alembic

# Tạo migration từ models
alembic revision --autogenerate -m "create users and posts tables"

# Chạy migration
alembic upgrade head

# Xem lịch sử migrations
alembic history
```

**Cần cấu hình** `alembic/env.py` để:

1. Import tất cả models (để autogenerate biết các tables)
2. Dùng async engine

---

## ✅ Checklist

- [ ] Giải thích được sự khác biệt SQLAlchemy Model vs Pydantic Schema
- [ ] Tạo được Comment model với self-referential relationship
- [ ] Tạo Post schemas với nested schema
- [ ] Viết slug generator
- [ ] Setup và chạy được Alembic migration

---

➡️ **Tiếp theo:** [Module 03 — Repository Pattern & CRUD](../module_03/README.md)
