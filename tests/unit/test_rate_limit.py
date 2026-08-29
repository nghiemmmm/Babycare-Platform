"""
Test Rate Limiter: Redis Lua script & Trusted Proxy Real IP
"""
from fastapi import Request
import pytest
from app.core.rate_limit import get_real_client_ip, check_rate_limit
from app.shared.exceptions import RateLimitExceededError


def test_get_real_client_ip_with_trusted_proxy():
    """Kiểm tra bóc tách IP thật của Client đằng sau Nginx/Cloudflare"""
    scope = {
        "type": "http",
        "client": ("127.0.0.1", 12345),
        "headers": [
            (b"x-forwarded-for", b"203.0.113.195, 10.0.0.1"),
            (b"cf-connecting-ip", b"203.0.113.195")
        ]
    }
    req = Request(scope)
    assert get_real_client_ip(req) == "203.0.113.195"


def test_rate_limit_allows_normal_traffic_and_blocks_excess():
    """Kiểm tra giới hạn tần suất gọi API chống DoS"""
    key = "test_rate_user_unique"
    # Gọi lần 1 trong giới hạn
    check_rate_limit(key, max_attempts=2, window_seconds=60)
    # Gọi lần 2 trong giới hạn
    check_rate_limit(key, max_attempts=2, window_seconds=60)
    
    # Gọi lần 3 vượt giới hạn -> Phải raise RateLimitExceededError
    with pytest.raises(RateLimitExceededError):
        check_rate_limit(key, max_attempts=2, window_seconds=60)
