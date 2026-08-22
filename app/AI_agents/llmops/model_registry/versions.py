import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)


class ModelVersions:
    """
    Quản lý các Version Aliases và ánh xạ phiên bản mô hình AI trong hệ thống.
    Giúp chuyển đổi phiên bản mô hình linh hoạt mà không cần sửa code ứng dụng.
    """
    FAST_LITE = "gemini-3.5-flash-lite"
    DEFAULT_FLASH = "gemini-2.0-flash"
    HIGH_PRO = "gemini-1.5-pro"

    _ALIAS_MAP: Dict[str, str] = {
        "fast": FAST_LITE,
        "lite": FAST_LITE,
        "default": DEFAULT_FLASH,
        "standard": DEFAULT_FLASH,
        "high": HIGH_PRO,
        "pro": HIGH_PRO,
        "reasoning": HIGH_PRO
    }

    @classmethod
    def get_model_by_alias(cls, alias: str) -> str:
        """Lấy tên mô hình thực tế theo alias định nghĩa."""
        clean_alias = alias.strip().lower()
        return cls._ALIAS_MAP.get(clean_alias, cls.DEFAULT_FLASH)

    @classmethod
    def register_alias(cls, alias: str, model_name: str):
        """Đăng ký hoặc ghi đè một Version Alias mới."""
        cls._ALIAS_MAP[alias.strip().lower()] = model_name
