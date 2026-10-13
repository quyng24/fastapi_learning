# 🚀 FastAPI Backend Architecture — Lộ Trình Học Thực Chiến

> Dự án học FastAPI từ cơ bản đến nâng cao, theo đúng kiến trúc **Production-Ready** được dùng trong các dự án thực tế lớn.

---

## 🎯 Mục Tiêu Sau Khi Hoàn Thành

- Hiểu rõ **luồng dữ liệu** từ Request → Router → Service → Repository → Database → Response
- Áp dụng **Clean Architecture / Layered Architecture** đúng chuẩn
- Làm việc được với **dự án lớn** nhiều module, nhiều team
- Biết cách viết **code dễ test, dễ bảo trì, dễ mở rộng**

---

## 📦 Công Nghệ Sử Dụng

| Công nghệ         | Mục đích                   |
| ----------------- | -------------------------- |
| FastAPI           | Web framework async        |
| SQLAlchemy 2.0    | ORM - tương tác database   |
| Alembic           | Migration database         |
| Pydantic v2       | Validation & serialization |
| JWT (python-jose) | Authentication             |
| Redis             | Caching & session          |
| PostgreSQL        | Database chính             |
| pytest            | Testing                    |

---

## 📚 Lộ Trình Học (6 Modules)

| Module                                     | Chủ đề                                    | Thời gian ước tính |
| ------------------------------------------ | ----------------------------------------- | ------------------ |
| [Module 01](exercises/module_01/README.md) | Cấu trúc dự án & App Bootstrap            | 1-2 ngày           |
| [Module 02](exercises/module_02/README.md) | Models, Schemas & Database Layer          | 2-3 ngày           |
| [Module 03](exercises/module_03/README.md) | Repository Pattern & CRUD                 | 2-3 ngày           |
| [Module 04](exercises/module_04/README.md) | Service Layer & Business Logic            | 2-3 ngày           |
| [Module 05](exercises/module_05/README.md) | Authentication, Dependencies & Middleware | 3-4 ngày           |
| [Module 06](exercises/module_06/README.md) | Testing, Error Handling & Production      | 2-3 ngày           |

---

## 🏗️ Kiến Trúc Tổng Quan

```
📥 HTTP Request
      │
      ▼
┌─────────────┐
│  Middleware  │  ← Logging, CORS, Rate Limit, Auth check
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │  ← Định tuyến URL, khai báo HTTP method
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Dependency  │  ← Inject DB session, Current User, Permissions
│  Injection  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Service    │  ← Business logic, validation nghiệp vụ
│   Layer     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Repository  │  ← Tương tác database, queries
│   Layer     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Database   │  ← PostgreSQL / MySQL / SQLite
└─────────────┘
```

---

## 🗂️ Cấu Trúc Thư Mục

```
fastapi-learning/
├── app/                        # Application code chính
│   ├── api/                    # Tầng API
│   │   └── v1/
│   │       ├── endpoints/      # Route handlers (controllers)
│   │       └── router.py       # API router tổng hợp
│   ├── core/                   # Cấu hình & cài đặt hệ thống
│   │   ├── config.py           # Settings từ biến môi trường
│   │   ├── database.py         # Kết nối database
│   │   └── security.py         # JWT, password hashing
│   ├── models/                 # SQLAlchemy ORM models (Database tables)
│   ├── schemas/                # Pydantic schemas (Request/Response DTOs)
│   ├── services/               # Business logic layer
│   ├── repositories/           # Data access layer (Database queries)
│   ├── dependencies/           # FastAPI dependencies (DI Container)
│   ├── middlewares/            # Custom middlewares
│   ├── exceptions/             # Custom exceptions & handlers
│   ├── utils/                  # Helper functions
│   └── main.py                 # App entry point
├── tests/                      # Test files
│   ├── unit/                   # Unit tests
│   └── integration/            # Integration tests
├── exercises/                  # Bài tập từng module
├── alembic/                    # Database migrations
├── docs/                       # Tài liệu bổ sung
├── .env.example                # Template biến môi trường
├── requirements.txt            # Dependencies
└── README.md
```

---

## 🚀 Bắt Đầu

Yêu cầu: Python 3.12 trở lên. Trong VS Code, chọn interpreter Python dùng cho terminal và workspace trước khi cài dependencies. Nếu không có file `.env`, app dùng SQLite local theo cấu hình mặc định.

1. Đọc [`exercises/module_01/README.md`](exercises/module_01/README.md) để bắt đầu
2. Làm theo từng bài tập, đối chiếu với code mẫu trong thư mục `app/`
3. Tự kiểm tra bằng cách chạy tests

```bash
# Cài dependencies
python -m pip install -r requirements.txt

# Chạy ứng dụng
python -m uvicorn app.main:app --reload

# Chạy tests
python -m pytest tests/ -v
```
