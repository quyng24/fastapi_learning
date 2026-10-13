"""
app/core/config.py
==================
Quản lý cấu hình ứng dụng sử dụng Pydantic Settings.

Pydantic Settings tự động đọc giá trị từ:
1. Biến môi trường (environment variables)
2. File .env (nếu có)
3. Giá trị mặc định trong code

Ưu điểm: Type-safe, tự validate, không cần đọc os.environ thủ công.
"""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Cấu hình ứng dụng.
    
    Mọi field ở đây đều có thể override bằng biến môi trường cùng tên.
    Ví dụ: APP_NAME=MyApp python main.py
    """
    
    # ===================================
    # App Settings
    # ===================================
    APP_NAME: str = "FastAPI Learning Project"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    
    # ===================================
    # Database
    # ===================================
    DATABASE_URL: str = "sqlite+aiosqlite:///./fastapi_learning.db"
    
    # ===================================
    # Security
    # ===================================
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # ===================================
    # Redis (Optional)
    # ===================================
    REDIS_URL: str | None = None
    
    # ===================================
    # CORS
    # ===================================
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # ===================================
    # Pagination
    # ===================================
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    # ===================================
    # Pydantic Settings Config
    # ===================================
    model_config = SettingsConfigDict(
        env_file=".env",          # Đọc từ file .env
        env_file_encoding="utf-8",
        case_sensitive=True,       # DATABASE_URL ≠ database_url
        extra="ignore",            # Bỏ qua các biến môi trường không khai báo
    )

    # ===================================
    # Validators
    # ===================================
    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: str | list) -> list[str]:
        """
        Cho phép ALLOWED_ORIGINS được set dưới dạng string JSON hoặc list.
        
        Trong .env file: ALLOWED_ORIGINS=["http://localhost:3000"]
        """
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """
        Kiểm tra cấu hình hợp lệ cho production.
        
        BẢNG HỌC: model_validator chạy SAU KHI tất cả fields được validate,
        nên bạn có thể kiểm tra mối quan hệ giữa các fields ở đây.
        """
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY == "change-me-in-production-use-openssl-rand-hex-32":
                raise ValueError("Must set a proper SECRET_KEY in production!")
            if self.DEBUG:
                raise ValueError("DEBUG must be False in production!")
        return self


# ===================================
# Singleton Pattern với lru_cache
# ===================================
@lru_cache()
def get_settings() -> Settings:
    """
    Trả về singleton instance của Settings.
    
    lru_cache() đảm bảo Settings chỉ được tạo MỘT LẦN duy nhất.
    Điều này quan trọng vì:
    1. Tránh đọc .env file nhiều lần (performance)
    2. Đảm bảo toàn app dùng cùng 1 config object
    
    Trong tests, bạn có thể override bằng:
        app.dependency_overrides[get_settings] = lambda: test_settings
    """
    return Settings()


# Shortcut để import trực tiếp (dùng trong module-level code)
settings = get_settings()

