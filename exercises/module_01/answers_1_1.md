# Bài 1.1 — Đọc và Phân Tích

### 1. `lifespan` function dùng để làm gì? Tại sao không dùng `@app.on_event("startup")` cũ?

- `lifespan` quản lý vòng đời ứng dụng bằng một async context manager: phần trước `yield` chạy khi khởi động, phần sau `yield` chạy khi tắt ứng dụng.
- Cách này đặt khởi tạo và dọn dẹp tài nguyên trong cùng một luồng điều khiển. Các event handler `on_event` cũ đã được thay thế trong hướng dẫn FastAPI bằng lifespan.
- Trong project này, lifespan tạo bảng khi chạy development. `app.state.settings` là nơi lưu cấu hình để các thành phần của app dùng chung; đây không phải lợi ích tự động riêng của lifespan.

### 2. Tại sao `include_router` được gọi với `prefix="/api/v1"`? Lợi ích của API versioning là gì?

- Việc sử dụng include_router với prefix="/api/v1" là một trong những tiêu chuẩn thiết kế (best practices) quan trọng nhất khi xây dựng RESTful API. Prefix ghép vào đường dẫn của các endpoint trong router; ví dụ router users tạo đường dẫn bắt đầu bằng `/api/v1`. Health check có cả đường dẫn `/health` và `/api/v1/health`.
- Versioning cho phép duy trì hợp đồng API cũ trong khi phát triển phiên bản mới, giúp client có thời gian nâng cấp và giảm nguy cơ thay đổi làm hỏng client hiện hữu. URL versioning là một lựa chọn phổ biến, không phải quy tắc bắt buộc cho mọi API.

### 3. Middleware được thêm theo thứ tự nào? Thứ tự đó có ảnh hưởng gì không?

- Starlette áp dụng middleware theo LIFO: middleware được thêm sau chạy trước trên request và chạy sau trên response.
- Trong `main.py`, logging được thêm trước, sau đó đến CORS. Vì vậy CORS bao ngoài logging trong nhóm user middleware: request đi qua CORS rồi logging; response đi qua logging rồi CORS.
- Thứ tự ảnh hưởng đến middleware nào nhìn thấy request/response trước. CORS ngoài logging giúp thêm CORS headers cho các response được xử lý trong stack này. Các lỗi 500 chưa được xử lý có thể được tạo bởi lớp `ServerErrorMiddleware` ở ngoài user middleware; muốn CORS bao phủ cả trường hợp đó cần bọc toàn bộ ASGI app bằng CORS middleware.

# Bài 1.2 — Config với Environment Variables

1. `MAX_LOGIN_ATTEMPTS: int = 5` — Hoàn thành.
2. `MAINTENANCE_MODE: bool = False` — Hoàn thành.
3. Validator từ chối `DEBUG=True` khi `ENVIRONMENT="production"` — Hoàn thành.

Kiểm tra bằng lệnh trong đề. Giá trị được nạp từ `.env` có thể khác giá trị mặc định trong code; không nên lưu hoặc chia sẻ toàn bộ `model_dump()` vì có thể chứa `SECRET_KEY`.

# Bài 1.3 — Custom Health Check

1. Health endpoint được đăng ký qua router v1.
2. Endpoint thực thi `SELECT 1` để kiểm tra database; nếu database không khả dụng, trả HTTP 503 thay vì báo connected giả.
3. `/health` trả `status`, `version`, `environment`, `database` và `timestamp` UTC. Router v1 cũng cung cấp `/api/v1/health`.

# Bài 1.4 — App Factory Pattern

Hoàn thành. `create_app()` dùng settings mặc định khi không truyền đối số và vẫn nhận settings tùy chỉnh để tạo app cho test.

## Checklist Hoàn Thành Module 01

- [x] Giải thích được tại sao cần chia code thành layers
- [x] Hiểu luồng request đi qua các layers như thế nào
- [x] Biết cách dùng Pydantic Settings để quản lý config
- [x] Biết cách tạo SQLAlchemy async engine và session
- [x] Hoàn thành Bài 1.1, 1.2, 1.3
- [x] (Nâng cao) Hoàn thành Bài 1.4
