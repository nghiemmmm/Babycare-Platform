"""
Backward compatibility layer for app.shared.rate_limit.
All rate limiting core logic has been moved to app.core.rate_limit.
"""

from app.core.rate_limit import (
    check_rate_limit,
    rate_limiter,
    rate_limit,
    get_real_client_ip,
    is_trusted_proxy,
    normalize_identifier,
    build_rate_limit_key,
    _memory_counters,
    _memory_lock,
    _check_in_memory,
    _REDIS_RATE_LIMIT_LUA,
)

__all__ = [
    "check_rate_limit",
    "rate_limiter",
    "rate_limit",
    "get_real_client_ip",
    "is_trusted_proxy",
    "normalize_identifier",
    "build_rate_limit_key",
    "_memory_counters",
    "_memory_lock",
    "_check_in_memory",
    "_REDIS_RATE_LIMIT_LUA",
]
