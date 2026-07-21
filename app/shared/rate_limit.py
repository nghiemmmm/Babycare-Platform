"""
Rate Limiting Module

Giới hạn số lần gọi cho các endpoint nhạy cảm (login/register/forgot-password) theo IP,
chống brute-force mật khẩu và spam email. Ưu tiên dùng Redis (INCR + EXPIRE, chia sẻ được
giữa nhiều instance); nếu Redis chưa cấu hình/không kết nối được thì fallback sang bộ đếm
trong bộ nhớ tiến trình (chỉ áp dụng cho 1 instance, mất khi restart) - vẫn tốt hơn là tắt
hẳn rate limit, khác với pattern fail-open "bỏ qua hoàn toàn" của cache Redis thông thường
vì đây là một control bảo mật, không phải tối ưu hiệu năng.
"""
import logging
import threading
import time
from typing import Dict, Tuple

from fastapi import Request

from app.infrastructure.cache import redis as cache
from app.shared.concurrency import run_in_threadpool
from app.shared.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)

_memory_counters: Dict[str, Tuple[int, float]] = {}
_memory_lock = threading.Lock()


def _check_in_memory(key: str, max_attempts: int, window_seconds: int) -> None:
    """Đếm số lần gọi trong bộ nhớ tiến trình khi Redis không khả dụng."""
    now = time.monotonic()
    with _memory_lock:
        count, expires_at = _memory_counters.get(key, (0, now + window_seconds))
        if now >= expires_at:
            count, expires_at = 0, now + window_seconds
        count += 1
        _memory_counters[key] = (count, expires_at)

    if count > max_attempts:
        raise RateLimitExceededError()


def check_rate_limit(key: str, max_attempts: int, window_seconds: int) -> None:
    """
    Tăng bộ đếm cho `key` và raise RateLimitExceededError nếu vượt quá `max_attempts`
    trong `window_seconds`. Dùng Redis nếu có, tự động fallback sang bộ đếm trong bộ nhớ.
    """
    client = cache.get_client()
    if client is not None:
        try:
            count = client.incr(key)
            if count == 1:
                client.expire(key, window_seconds)
            if count > max_attempts:
                raise RateLimitExceededError()
            return
        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.warning(f"Lỗi đọc/ghi rate limit trên Redis cho key '{key}': {e}. Dùng fallback bộ nhớ.")

    _check_in_memory(key, max_attempts, window_seconds)


def rate_limiter(action: str, max_attempts: int, window_seconds: int):
    """
    Tạo một FastAPI dependency giới hạn `max_attempts` lần gọi trong `window_seconds`
    giây cho mỗi địa chỉ IP, theo tên `action` (vd. "login", "register").
    """

    async def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{action}:{client_ip}"
        await run_in_threadpool(check_rate_limit, key, max_attempts, window_seconds)

    return dependency
