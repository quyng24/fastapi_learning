"""
app/api/v1/router.py
=====================
API v1 Router — Tập hợp tất cả endpoints của version 1.

BẢNG HỌC: API Versioning
==========================
Tại sao cần version API?
- Khi thay đổi API interface (rename fields, thay đổi behavior)
- Client cũ vẫn dùng /api/v1 và không bị ảnh hưởng
- Client mới dùng /api/v2 với features mới

Cách implement:
- URL path versioning: /api/v1/, /api/v2/ (phổ biến nhất)
- Header versioning: Accept: application/vnd.api+json;version=1
- Query param: /api/users?version=1
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, users

# Router cho toàn bộ API v1
api_v1_router = APIRouter()

# Đăng ký các sub-routers
api_v1_router.include_router(auth.router)
api_v1_router.include_router(users.router)

# Khi thêm module mới:
# from app.api.v1.endpoints import posts
# api_v1_router.include_router(posts.router)

