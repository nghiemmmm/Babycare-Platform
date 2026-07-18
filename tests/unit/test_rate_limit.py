from unittest.mock import patch, MagicMock
import pytest
from app.shared.exceptions import RateLimitExceededError
from app.shared import rate_limit


@pytest.fixture(autouse=True)
def clear_memory_counters():
    rate_limit._memory_counters.clear()
    yield
    rate_limit._memory_counters.clear()


def test_check_rate_limit_uses_redis_when_available():
    mock_client = MagicMock()
    mock_client.incr.side_effect = [1, 2, 3]

    with patch("app.shared.rate_limit.cache.get_client", return_value=mock_client):
        rate_limit.check_rate_limit("key1", max_attempts=3, window_seconds=60)
        rate_limit.check_rate_limit("key1", max_attempts=3, window_seconds=60)
        rate_limit.check_rate_limit("key1", max_attempts=3, window_seconds=60)

    mock_client.expire.assert_called_once_with("key1", 60)


def test_check_rate_limit_raises_when_redis_count_exceeds_max():
    mock_client = MagicMock()
    mock_client.incr.return_value = 4

    with patch("app.shared.rate_limit.cache.get_client", return_value=mock_client):
        with pytest.raises(RateLimitExceededError):
            rate_limit.check_rate_limit("key1", max_attempts=3, window_seconds=60)


def test_check_rate_limit_falls_back_to_memory_when_redis_errors():
    mock_client = MagicMock()
    mock_client.incr.side_effect = Exception("connection lost")

    with patch("app.shared.rate_limit.cache.get_client", return_value=mock_client):
        # Không raise dù Redis lỗi, vì fallback bộ nhớ vẫn cho phép lần gọi đầu tiên.
        rate_limit.check_rate_limit("key2", max_attempts=1, window_seconds=60)


def test_check_rate_limit_in_memory_allows_up_to_max_attempts():
    with patch("app.shared.rate_limit.cache.get_client", return_value=None):
        rate_limit.check_rate_limit("key3", max_attempts=2, window_seconds=60)
        rate_limit.check_rate_limit("key3", max_attempts=2, window_seconds=60)
        with pytest.raises(RateLimitExceededError):
            rate_limit.check_rate_limit("key3", max_attempts=2, window_seconds=60)


def test_check_rate_limit_in_memory_resets_after_window_expires():
    with patch("app.shared.rate_limit.cache.get_client", return_value=None):
        with patch("app.shared.rate_limit.time.monotonic", return_value=1000.0):
            rate_limit.check_rate_limit("key4", max_attempts=1, window_seconds=60)

        with patch("app.shared.rate_limit.time.monotonic", return_value=1061.0):
            # Đã qua cửa sổ 60s, bộ đếm phải reset thay vì raise
            rate_limit.check_rate_limit("key4", max_attempts=1, window_seconds=60)
