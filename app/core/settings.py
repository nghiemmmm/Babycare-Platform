import os
from typing import Optional
from pydantic import model_validator
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

    # Rate Limiting Configuration
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_TRUSTED_PROXIES: list[str] = ["127.0.0.1", "::1"]
    RATE_LIMIT_DEFAULT_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_DEFAULT_WINDOW_SECONDS: int = 300
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 300
    RATE_LIMIT_LOGIN_EMAIL_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_EMAIL_WINDOW_SECONDS: int = 900
    RATE_LIMIT_REGISTER_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = 600
    RATE_LIMIT_REFRESH_MAX_ATTEMPTS: int = 20
    RATE_LIMIT_REFRESH_WINDOW_SECONDS: int = 300
    RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS: int = 600
    RATE_LIMIT_VERIFY_OTP_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_VERIFY_OTP_WINDOW_SECONDS: int = 600
    RATE_LIMIT_RESET_PASSWORD_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_RESET_PASSWORD_WINDOW_SECONDS: int = 600

    # Timeout tối đa (giây) cho các call đồng bộ (Firebase/Firestore/RAG) chạy trong threadpool
    THREADPOOL_TIMEOUT_SECONDS: int = 30

    # URL gốc của frontend, dùng để tạo action link khi cần (vd. reset password)
    FRONTEND_URL: str = "http://localhost:5173"

    # SMTP Configuration (tùy chọn - nếu bỏ trống, gửi email quên mật khẩu fail-open:
    # chỉ log warning, không chặn luồng/không lộ cho client biết email có gửi được không)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None

    # AI API Keys & LLM Provider Settings
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    LLM_PROVIDER: str = "openrouter"  # "openrouter", "gemini", "openai"
    OPENROUTER_MODEL: str = "google/gemini-3.5-flash-001"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_RETRIES: int = 2

    # Cloudinary (tùy chọn - nếu bỏ trống, ảnh đại diện bé và file ghi âm tiếng khóc
    # fail-open sang lưu trên đĩa local app/static/, giống nguyên tắc SMTP/Redis)
    CLOUDINARY_CLOUD_NAME: Optional[str] = None
    CLOUDINARY_API_KEY: Optional[str] = None
    CLOUDINARY_API_SECRET: Optional[str] = None

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        """Production Guard: Ngăn chặn cấu hình mất an toàn trên môi trường Production."""
        if self.APP_ENV.lower() == "production" and self.DEBUG is True:
            raise ValueError(
                "Production Guard Alert: DEBUG không được phép bật (True) khi APP_ENV='production'. "
                "Vui lòng thiết lập DEBUG=false để đảm bảo an toàn bảo mật."
            )
        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
