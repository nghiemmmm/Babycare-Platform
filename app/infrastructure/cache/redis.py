"""
Redis Cache Module

Cung cấp một lớp cache mỏng, fail-open: nếu Redis chưa được cấu hình hoặc
không thể kết nối, mọi thao tác cache coi như cache-miss thay vì làm lỗi
request. Dùng cho dữ liệu đọc nhiều, ít thay đổi, và cho rate limiting
(vd. login/register/forgot-password) để giảm số lượt đọc Firestore.
"""
import json
import logging
from typing import Optional

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional["redis.Redis"] = None
_client_initialized = False


def _get_client() -> Optional["redis.Redis"]:
    """
    Khởi tạo và trả về Redis client dạng singleton.

    Trả về None nếu chưa cấu hình REDIS_URL hoặc không thể kết nối, để toàn
    bộ cache fail-open thay vì làm sập ứng dụng khi Redis không sẵn sàng.
    """
    global _client, _client_initialized
    if _client_initialized:
        return _client

    _client_initialized = True
    if not settings.REDIS_URL:
        logger.info("REDIS_URL chưa được cấu hình - bỏ qua cache, luôn đọc thẳng Firestore.")
        return None

    try:
        candidate = redis.Redis.from_url(
            settings.REDIS_URL, socket_timeout=1, socket_connect_timeout=1
        )
        candidate.ping()
        _client = candidate
    except Exception as e:
        logger.warning(f"Không thể kết nối Redis ({settings.REDIS_URL}): {e}. Cache sẽ bị bỏ qua (fail-open).")
        _client = None

    return _client


def get_client() -> Optional["redis.Redis"]:
    """Trả về Redis client dùng chung (singleton, fail-open) cho các module khác (vd. rate limiting)."""
    return _get_client()


def get_json(key: str) -> Optional[dict]:
    """Lấy một giá trị JSON từ cache. Trả về None nếu cache-miss hoặc Redis không khả dụng."""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as e:
        logger.warning(f"Lỗi đọc cache Redis cho key '{key}': {e}")
        return None


def set_json(key: str, value: dict, ttl_seconds: int) -> None:
    """Ghi một giá trị JSON vào cache kèm TTL. Không làm gì nếu Redis không khả dụng."""
    client = _get_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value))
    except Exception as e:
        logger.warning(f"Lỗi ghi cache Redis cho key '{key}': {e}")


def delete(key: str) -> None:
    """Xóa một key khỏi cache. Không làm gì nếu Redis không khả dụng."""
    client = _get_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception as e:
        logger.warning(f"Lỗi xóa cache Redis cho key '{key}': {e}")
