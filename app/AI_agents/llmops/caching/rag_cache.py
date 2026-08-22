import time
import logging
from collections import OrderedDict
from typing import Optional, Dict, Any, Tuple

logger = logging.getLogger(__name__)


class RAGCacheManager:
    """
    Quản lý bộ nhớ đệm In-Memory (LRU Cache) kết quả tra cứu và nén ngữ cảnh RAG WHO.
    Sử dụng OrderedDict để loại bỏ các entry ít dùng nhất (LRU eviction) thay vì xóa sạch toàn bộ.
    """
    # Key -> (value, expire_at_timestamp)
    _cache: OrderedDict[str, Tuple[str, float]] = OrderedDict()
    _hits: int = 0
    _misses: int = 0
    _max_entries: int = 500
    _default_ttl: int = 86400  # 24h

    @classmethod
    def generate_key(cls, query: str, k: int = 3, domain: Optional[str] = None, max_tokens: int = 800) -> str:
        """Tạo chìa khóa đệm độc nhất theo câu hỏi và tham số tra cứu."""
        return f"{query.strip().lower()}_{k}_{domain}_{max_tokens}"

    @classmethod
    def get(cls, key: str) -> Optional[str]:
        """Lấy kết quả từ Cache. Tăng đếm hits/misses và làm mới vị trí LRU."""
        now = time.time()
        if key in cls._cache:
            val, expire_at = cls._cache[key]
            if expire_at > 0 and now > expire_at:
                # Đã hết hạn TTL
                del cls._cache[key]
                cls._misses += 1
                return None
            
            # Move to most recently used
            cls._cache.move_to_end(key)
            cls._hits += 1
            return val
        
        cls._misses += 1
        return None

    @classmethod
    def set(cls, key: str, value: str, ttl_seconds: Optional[int] = None):
        """Lưu kết quả vào Cache. Tự động đẩy phần tử cũ nhất nếu vượt quá max_entries (LRU)."""
        ttl = ttl_seconds if ttl_seconds is not None else cls._default_ttl
        expire_at = time.time() + ttl if ttl > 0 else 0.0

        if key in cls._cache:
            cls._cache.move_to_end(key)
        elif len(cls._cache) >= cls._max_entries:
            # Loại bỏ entry cũ nhất (LRU)
            cls._cache.popitem(last=False)

        cls._cache[key] = (value, expire_at)

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Thống kê chỉ số Hits, Misses, và Tỷ lệ Hit Rate (%) của RAG Cache."""
        total = cls._hits + cls._misses
        hit_rate = round((cls._hits / total * 100), 2) if total > 0 else 0.0
        return {
            "hits": cls._hits,
            "misses": cls._misses,
            "hit_rate_pct": hit_rate,
            "size": len(cls._cache),
            "max_entries": cls._max_entries
        }

    @classmethod
    def clear(cls):
        """Xóa sạch cache đệm."""
        cls._cache.clear()
        cls._hits = 0
        cls._misses = 0

