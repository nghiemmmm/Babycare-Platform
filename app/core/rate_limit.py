"""
Core Rate Limiting Module for BabyCare AI

Provides enterprise-grade, distributed rate limiting with:
1. Real Client IP resolution with trusted proxy verification (chống IP spoofing).
2. Atomic Redis operations (INCR + EXPIRE via Lua script, chống key không có TTL).
3. Thread-safe in-memory fallback with automatic cleanup (chống memory leak).
4. Multi-identifier support (IP, User ID, Normalized Email).
5. Clean FastAPI Dependency injection with Retry-After header support.
"""

import ipaddress
import logging
import threading
import time
from typing import Callable, Dict, List, Optional, Tuple

from fastapi import Request

from app.core.config import settings
from app.infrastructure.cache import redis as cache
from app.shared.concurrency import run_in_threadpool
from app.shared.exceptions import RateLimitExceededError

logger = logging.getLogger(__name__)

# Bộ đếm trong bộ nhớ khi Redis không khả dụng
_memory_counters: Dict[str, Tuple[int, float]] = {}
_memory_lock = threading.Lock()
_LAST_CLEANUP_TIME = 0.0
_CLEANUP_INTERVAL_SECONDS = 60.0

# Lua script atomic cho Redis để đảm bảo luôn có TTL và trả về chính xác retry_after
_REDIS_RATE_LIMIT_LUA = """
local current = redis.call('INCR', KEYS[1])
if tonumber(current) == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
if ttl == -1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
    ttl = tonumber(ARGV[1])
end
return {current, ttl}
"""


def is_trusted_proxy(client_host: str, trusted_proxies: Optional[List[str]] = None) -> bool:
    """
    Kiểm tra xem địa chỉ IP kết nối trực tiếp có nằm trong danh sách Trusted Proxies hay không.
    Hỗ trợ cả địa chỉ IP đơn lẻ (127.0.0.1, ::1) và dải mạng CIDR (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16).
    """
    if not client_host or client_host == "unknown":
        return False

    proxies = trusted_proxies if trusted_proxies is not None else settings.RATE_LIMIT_TRUSTED_PROXIES
    if not proxies:
        return False

    try:
        client_addr = ipaddress.ip_address(client_host)
    except ValueError:
        return False

    for proxy_pattern in proxies:
        proxy_pattern = proxy_pattern.strip()
        if not proxy_pattern:
            continue
        try:
            if "/" in proxy_pattern:
                if client_addr in ipaddress.ip_network(proxy_pattern, strict=False):
                    return True
            else:
                if client_addr == ipaddress.ip_address(proxy_pattern):
                    return True
        except ValueError:
            continue

    return False


def get_real_client_ip(request: Request, trusted_proxies: Optional[List[str]] = None) -> str:
    """
    Trích xuất IP thật của client một cách an toàn.
    Chỉ tin tưởng forwarded headers (CF-Connecting-IP, X-Forwarded-For, X-Real-IP)
    KHI VÀ CHỈ KHI kết nối trực tiếp (request.client.host) đến từ Trusted Proxy.
    """
    if not request.client or not request.client.host:
        return "unknown"

    direct_host = request.client.host.strip()

    # Nếu không phải trusted proxy -> TUYỆT ĐỐI KHÔNG tin tưởng forwarded headers
    if not is_trusted_proxy(direct_host, trusted_proxies):
        return direct_host

    # 1. Ưu tiên Cloudflare header nếu có
    cf_connecting_ip = request.headers.get("CF-Connecting-IP")
    if cf_connecting_ip:
        candidate = cf_connecting_ip.strip()
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            pass

    # 2. Kiểm tra X-Forwarded-For (lấy client IP đầu tiên hợp lệ)
    x_forwarded_for = request.headers.get("X-Forwarded-For")
    if x_forwarded_for:
        parts = [p.strip() for p in x_forwarded_for.split(",") if p.strip()]
        if parts:
            candidate = parts[0]
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                pass

    # 3. Kiểm tra X-Real-IP
    x_real_ip = request.headers.get("X-Real-IP")
    if x_real_ip:
        candidate = x_real_ip.strip()
        try:
            ipaddress.ip_address(candidate)
            return candidate
        except ValueError:
            pass

    return direct_host


def normalize_identifier(identifier_type: str, raw_value: str) -> str:
    """
    Chuẩn hóa định danh (IP, Email, User ID) để tránh bypass do khoảng trắng hoặc chữ hoa/thường.
    """
    if not raw_value:
        return "unknown"
    val = raw_value.strip()
    if identifier_type.lower() == "email":
        return val.lower()
    return val


def build_rate_limit_key(action: str, identifier_type: str, identifier_value: str) -> str:
    """Tạo key rate limit chuẩn hóa: ratelimit:{action}:{type}:{normalized_value}"""
    normalized = normalize_identifier(identifier_type, identifier_value)
    return f"ratelimit:{action}:{identifier_type}:{normalized}"


def _cleanup_memory_counters_unlocked(now: float) -> None:
    """Dọn dẹp các key đã hết hạn trong bộ nhớ."""
    global _LAST_CLEANUP_TIME
    if now - _LAST_CLEANUP_TIME < _CLEANUP_INTERVAL_SECONDS and len(_memory_counters) < 1000:
        return
    _LAST_CLEANUP_TIME = now
    expired_keys = [k for k, (_, exp) in _memory_counters.items() if now >= exp]
    for k in expired_keys:
        del _memory_counters[k]


def _check_in_memory(key: str, max_attempts: int, window_seconds: int) -> Tuple[int, int]:
    """
    Đếm số lần gọi trong bộ nhớ tiến trình (Thread-safe).
    Trả về (current_count, retry_after_seconds).
    """
    now = time.monotonic()
    with _memory_lock:
        _cleanup_memory_counters_unlocked(now)
        count, expires_at = _memory_counters.get(key, (0, now + window_seconds))
        if now >= expires_at:
            count = 0
            expires_at = now + window_seconds
        count += 1
        _memory_counters[key] = (count, expires_at)
        retry_after = max(1, int(expires_at - now))

    return count, retry_after


def check_rate_limit(
    key: str,
    max_attempts: int,
    window_seconds: int,
    action: str = "request",
    identifier_type: str = "ip",
    identifier_value: str = "",
) -> None:
    """
    Tăng bộ đếm cho `key` và raise RateLimitExceededError nếu vượt quá `max_attempts`.
    Ưu tiên Redis (atomic Lua script). Tự động fallback an toàn sang In-memory nếu Redis lỗi/chưa cấu hình.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return

    count: int = 0
    retry_after: int = window_seconds

    client = cache.get_client()
    if client is not None:
        try:
            res = client.eval(_REDIS_RATE_LIMIT_LUA, 1, key, window_seconds)
            if isinstance(res, (list, tuple)) and len(res) >= 2:
                count = int(res[0])
                ttl = int(res[1])
                retry_after = max(1, ttl) if ttl > 0 else window_seconds
            else:
                count = int(res) if res is not None else 1
        except Exception as e:
            logger.warning(
                f"[RateLimit] Lỗi Redis khi kiểm tra key '{key}': {e}. Chuyển sang fallback bộ nhớ (In-memory)."
            )
            count, retry_after = _check_in_memory(key, max_attempts, window_seconds)
    else:
        count, retry_after = _check_in_memory(key, max_attempts, window_seconds)

    if count > max_attempts:
        # Ghi log bảo mật (không log mật khẩu hay dữ liệu nhạy cảm)
        safe_id = identifier_value
        if identifier_type == "email" and "@" in identifier_value:
            user_part, domain_part = identifier_value.split("@", 1)
            safe_id = f"{user_part[:2]}***@{domain_part}"

        logger.warning(
            f"[RateLimit Exceeded] Action: '{action}' | Type: '{identifier_type}' | ID: '{safe_id}' | "
            f"Count: {count}/{max_attempts} | Retry-After: {retry_after}s"
        )
        raise RateLimitExceededError(
            message="Bạn đã thực hiện quá nhiều yêu cầu. Vui lòng thử lại sau.",
            retry_after=retry_after,
        )


def _resolve_limits(action: str, max_attempts: Optional[int], window_seconds: Optional[int]) -> Tuple[int, int]:
    """Lấy cấu hình rate limit tương ứng với từng action từ settings nếu không được truyền trực tiếp."""
    if max_attempts is not None and window_seconds is not None:
        return max_attempts, window_seconds

    action_map = {
        "login": (settings.RATE_LIMIT_LOGIN_MAX_ATTEMPTS, settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS),
        "register": (settings.RATE_LIMIT_REGISTER_MAX_ATTEMPTS, settings.RATE_LIMIT_REGISTER_WINDOW_SECONDS),
        "refresh": (settings.RATE_LIMIT_REFRESH_MAX_ATTEMPTS, settings.RATE_LIMIT_REFRESH_WINDOW_SECONDS),
        "forgot-password": (
            settings.RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS,
            settings.RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS,
        ),
        "verify-reset-otp": (
            settings.RATE_LIMIT_VERIFY_OTP_MAX_ATTEMPTS,
            settings.RATE_LIMIT_VERIFY_OTP_WINDOW_SECONDS,
        ),
        "reset-password": (
            settings.RATE_LIMIT_RESET_PASSWORD_MAX_ATTEMPTS,
            settings.RATE_LIMIT_RESET_PASSWORD_WINDOW_SECONDS,
        ),
    }

    default_attempts, default_window = action_map.get(
        action.lower(),
        (settings.RATE_LIMIT_DEFAULT_MAX_ATTEMPTS, settings.RATE_LIMIT_DEFAULT_WINDOW_SECONDS),
    )

    resolved_attempts = max_attempts if max_attempts is not None else default_attempts
    resolved_window = window_seconds if window_seconds is not None else default_window
    return resolved_attempts, resolved_window


def rate_limit(
    action: str,
    max_attempts: Optional[int] = None,
    window_seconds: Optional[int] = None,
    key_func: Optional[Callable[[Request], Optional[str]]] = None,
    identifier_type: str = "ip",
):
    """
    Tạo FastAPI dependency kiểm tra Rate Limit sạch sẽ và có thể tái sử dụng.

    Ví dụ:
        @router.post("/login", dependencies=[Depends(rate_limit("login"))])
        @router.post("/register", dependencies=[Depends(rate_limit("register", max_attempts=5, window_seconds=600))])
    """
    resolved_attempts, resolved_window = _resolve_limits(action, max_attempts, window_seconds)

    async def dependency(request: Request) -> None:
        if not settings.RATE_LIMIT_ENABLED:
            return

        if key_func is not None:
            raw_val = key_func(request)
            if raw_val:
                key = build_rate_limit_key(action, identifier_type, raw_val)
                await run_in_threadpool(
                    check_rate_limit,
                    key,
                    resolved_attempts,
                    resolved_window,
                    action,
                    identifier_type,
                    raw_val,
                )
                return

        # Mặc định theo IP client thật
        client_ip = get_real_client_ip(request)
        key = build_rate_limit_key(action, "ip", client_ip)
        await run_in_threadpool(
            check_rate_limit,
            key,
            resolved_attempts,
            resolved_window,
            action,
            "ip",
            client_ip,
        )

    return dependency


# Alias hỗ trợ backward compatibility
def rate_limiter(action: str, max_attempts: int, window_seconds: int):
    """Legacy helper compatibility."""
    return rate_limit(action, max_attempts=max_attempts, window_seconds=window_seconds)
