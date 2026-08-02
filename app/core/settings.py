import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "BabyCare AI"
    APP_ENV: str = "local"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None
    # Web API Key (khác service account key) - dùng để gọi Firebase Identity Toolkit
    # REST API cho đăng nhập/refresh token. Lấy tại Firebase Console > Project
    # Settings > General > Web API Key.
    FIREBASE_WEB_API_KEY: Optional[str] = None

    # Redis Cache Configuration (tùy chọn - nếu bỏ trống, cache/rate-limit tự fail-open
    # sang bộ đếm trong bộ nhớ tiến trình)
    REDIS_URL: Optional[str] = None
    BABY_CACHE_TTL_SECONDS: int = 60

    # Timeout tối đa (giây) cho các call đồng bộ (Firebase/Firestore) chạy trong threadpool
    THREADPOOL_TIMEOUT_SECONDS: int = 10

    # URL gốc của frontend, dùng để tạo action link khi cần (vd. reset password)
    FRONTEND_URL: str = "http://localhost:5173"

    # SMTP Configuration (tùy chọn - nếu bỏ trống, gửi email quên mật khẩu fail-open:
    # chỉ log warning, không chặn luồng/không lộ cho client biết email có gửi được không)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    # AI API Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Cloudinary (tùy chọn - nếu bỏ trống, ảnh đại diện bé và file ghi âm tiếng khóc
    # fail-open sang lưu trên đĩa local app/static/, giống nguyên tắc SMTP/Redis)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
