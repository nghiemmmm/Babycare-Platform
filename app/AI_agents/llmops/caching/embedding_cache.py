import hashlib
import logging
from collections import OrderedDict
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class EmbeddingCacheManager:
    """
    Quản lý bộ nhớ đệm In-Memory (LRU Cache) cho Vector Embeddings.
    Tự động loại bỏ các vector ít truy cập nhất khi đạt max_entries.
    """
    _cache: OrderedDict[str, List[float]] = OrderedDict()
    _hits: int = 0
    _misses: int = 0
    _max_entries: int = 1000

    @staticmethod
    def _hash_text(text: str) -> str:
        """Tạo mã băm SHA256 độc nhất cho chuỗi văn bản."""
        return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()

    @classmethod
    def get(cls, text: str) -> Optional[List[float]]:
        """Lấy vector embedding từ cache đệm và làm mới vị trí LRU."""
        key = cls._hash_text(text)
        if key in cls._cache:
            cls._cache.move_to_end(key)
            cls._hits += 1
            return cls._cache[key]
        
        cls._misses += 1
        return None

    @classmethod
    def set(cls, text: str, vector: List[float]):
        """Lưu vector embedding vào cache đệm. Loại bỏ entry cũ nhất nếu đầy."""
        key = cls._hash_text(text)
        if key in cls._cache:
            cls._cache.move_to_end(key)
        elif len(cls._cache) >= cls._max_entries:
            cls._cache.popitem(last=False)
            
        cls._cache[key] = vector

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Thống kê hits, misses, hit rate và kích thước cache."""
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
        """Xóa sạch cache đệm embedding."""
        cls._cache.clear()
        cls._hits = 0
        cls._misses = 0

