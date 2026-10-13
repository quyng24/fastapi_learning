# Module 01 — Cấu Trúc Dự Án & App Bootstrap

## 🎯 Mục Tiêu Module Này

Hiểu cách **khởi tạo** và **tổ chức** một dự án FastAPI đúng chuẩn từ đầu.

---

## 📖 Lý Thuyết Cần Nắm

### 1. Tại sao cần tổ chức code theo layers?

Trong dự án nhỏ, bạn có thể viết mọi thứ trong 1 file. Nhưng khi dự án lớn:

```
❌ Cách KHÔNG nên làm (monolithic file):
main.py  ← chứa tất cả: models, routes, business logic, database queries

✅ Cách NÊN làm (layered architecture):
app/
├── api/        ← Chỉ xử lý HTTP request/response
├── services/   ← Chỉ chứa business logic
├── repositories/ ← Chỉ tương tác database
└── models/     ← Chỉ định nghĩa cấu trúc dữ liệu
```

**Lợi ích:**

- Mỗi layer có **1 trách nhiệm** duy nhất (Single Responsibility)
- Dễ **test** từng phần độc lập
- Nhiều người có thể **làm việc song song** mà không conflict
- Dễ **thay thế** một phần (ví dụ: đổi database) mà không ảnh hưởng layer khác

### 2. Luồng Request trong FastAPI

```
[Client] → [Middleware] → [Router/Endpoint] → [Dependency] → [Service] → [Repository] → [DB]
                                                                              ↑
                                                                         (query data)
[Client] ← [Schema/Response] ← [Router/Endpoint] ← [Service] ← [Repository]
```

### 3. `main.py` — Entry Point của ứng dụng

File `main.py` là nơi:

- Tạo instance `FastAPI()`
- Đăng ký routers
- Đăng ký middleware
- Đăng ký event handlers (startup/shutdown)

---

## 💻 Code Mẫu Để Đọc Hiểu

Đọc các file sau theo thứ tự:

1. [`../../app/core/config.py`](../../app/core/config.py) — Cách quản lý config với Pydantic Settings
2. [`../../app/core/database.py`](../../app/core/database.py) — Kết nối database async
3. [`../../app/main.py`](../../app/main.py) — App entry point

---

## 📝 BÀI TẬP

### Bài 1.1 — Đọc và Phân Tích (30 phút)

Đọc file `app/main.py` và trả lời:

1. `lifespan` function dùng để làm gì? Tại sao không dùng `@app.on_event("startup")` cũ?
2. Tại sao `include_router` được gọi với `prefix="/api/v1"`? Lợi ích của API versioning là gì?
3. Middleware được thêm theo thứ tự nào? Thứ tự đó có ảnh hưởng gì không?

> **Ghi chú:** Viết câu trả lời vào file `exercises/module_01/answers_1_1.md`

---

### Bài 1.2 — Thực Hành: Config với Environment Variables (45 phút)

**Yêu cầu:** Copy file `.env.example` thành `.env` và chỉnh sửa `app/core/config.py` để:

1. Thêm setting `MAX_LOGIN_ATTEMPTS: int = 5`
2. Thêm setting `MAINTENANCE_MODE: bool = False`
3. Thêm validator: nếu `ENVIRONMENT == "production"` thì `DEBUG` phải là `False`

**Hint:**

```python
from pydantic import model_validator

@model_validator(mode="after")
def validate_production_settings(self) -> "Settings":
    if self.ENVIRONMENT == "production" and self.DEBUG:
        raise ValueError("DEBUG must be False in production!")
    return self
```

**Kiểm tra:** Chạy `python -c "from app.core.config import settings; print(settings.model_dump())"`

---

### Bài 1.3 — Thực Hành: Custom Health Check (1 giờ)

**Yêu cầu:** Tạo endpoint `/health` trả về:

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "environment": "development",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

**Các bước:**

1. Tạo file `app/api/v1/endpoints/health.py`
2. Viết hàm check database connection
3. Đăng ký router trong `app/api/v1/router.py`

---

### Bài 1.4 — Challenge: App Factory Pattern (nâng cao, 2 giờ)

**Vấn đề:** Trong môi trường test, bạn muốn tạo app với config khác (database khác, không có một số middleware).

**Yêu cầu:** Refactor `main.py` thành **App Factory Pattern**:

```python
def create_app(settings: Settings | None = None) -> FastAPI:
    """Factory function tạo FastAPI instance với config tùy chỉnh"""
    if settings is None:
        settings = get_settings()

    app = FastAPI(...)
    # setup middlewares
    # setup routers
    # setup exception handlers
    return app

app = create_app()
```

**Lợi ích:** Trong test, bạn có thể làm:

```python
def test_app():
    test_settings = Settings(DATABASE_URL="sqlite:///test.db", DEBUG=True)
    app = create_app(settings=test_settings)
    client = TestClient(app)
```

---

## ✅ Checklist Hoàn Thành Module 01

- [ ] Giải thích được tại sao cần chia code thành layers
- [ ] Hiểu luồng request đi qua các layers như thế nào
- [ ] Biết cách dùng Pydantic Settings để quản lý config
- [ ] Biết cách tạo SQLAlchemy async engine và session
- [ ] Hoàn thành Bài 1.1, 1.2, 1.3
- [ ] (Nâng cao) Hoàn thành Bài 1.4

---

## 🔗 Tài Liệu Tham Khảo

- [FastAPI Official Docs - Bigger Applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic Settings Management](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [SQLAlchemy 2.0 Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)

---

➡️ **Tiếp theo:** [Module 02 — Models, Schemas & Database Layer](../module_02/README.md)
