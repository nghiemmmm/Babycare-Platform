import time
import hashlib
import logging
from collections import OrderedDict
from typing import Optional, Dict, Any, Tuple

from app.infrastructure.cache import redis as cache_redis
from app.shared.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# Từ khóa y tế cấp cứu tuyệt đối KHÔNG cache (bắt buộc Live Reasoning / Emergency Warning)
EMERGENCY_RED_FLAGS = [
    "co giật", "khó thở", "tím tái", "li bì", "hôn mê", "bất tỉnh",
    "sốt cao co giật", "sặc sữa", "ngộ độc", "uống nhầm", "thở rít",
    "rút lõm lồng ngực", "nôn vọt", "mất nước nặng", "cấp cứu"
]

# Từ khóa dữ liệu cá nhân / nhật ký riêng của từng bé
PERSONAL_DATA_KEYWORDS = [
    "con tôi", "bé nhà tôi", "vừa bú", "vừa uống", "vừa đo",
    "nhật ký", "cân nặng hôm nay", "mấy giờ bú", "lịch sử khám",
    "hôm nay bé", "mấy ngày qua bé", "cho tôi xem lại", "vừa ghi"
]


class AgentResponseCacheManager:
    """
    Quản lý Response Caching 2 tầng (L1 In-Memory LRU + L2 Redis Cloud) cho AI Agent:
    - Pediatric Age-Bracket Isolation: Tách biệt tri thức theo mốc phát triển lứa tuổi.
    - Safety Bypass: Tự động từ chối cache với câu hỏi cấp cứu hoặc dữ liệu cá nhân.
    - Dual-tier: L1 LRU (< 1ms) + L2 Redis Cloud (~15ms, fail-open).
    """

    # L1 In-Memory LRU Cache: cache_key -> (response_dict, expire_at)
    _l1_cache: OrderedDict[str, Tuple[Dict[str, Any], float]] = OrderedDict()
    _l1_max_entries: int = 500
    _l1_hits: int = 0
    _l2_hits: int = 0
    _misses: int = 0
    _default_ttl: int = 3600  # 1 giờ

    @staticmethod
    def get_age_bracket(age_months: Optional[int]) -> str:
        """
        Phân nhóm độ tuổi chuẩn Nhi khoa để cô lập ngữ cảnh y tế:
        - 0-3 tháng: Sơ sinh (Neonatal & Early Infancy)
        - 4-6 tháng: Tiền ăn dặm (Pre-weaning)
        - 7-12 tháng: Ăn dặm (Weaning & Growth spurt)
        - 13-36 tháng: Tập đi (Toddler: 1-3 tuổi)
        - > 36 tháng: Mẫu giáo (Preschool: 3-5 tuổi)
        - None / Khác: Tri thức chung (general)
        """
        if age_months is None or age_months < 0:
            return "general"
        if age_months <= 3:
            return "0_3m"
        if age_months <= 6:
            return "4_6m"
        if age_months <= 12:
            return "7_12m"
        if age_months <= 36:
            return "1_3y"
        return "3_5y"

    @classmethod
    def is_cacheable(cls, query: str, baby_id: Optional[str] = None, is_emergency: bool = False) -> Tuple[bool, str]:
        """
        Kiểm tra câu hỏi có đủ điều kiện an toàn để áp dụng Response Cache hay không.
        Trả về (is_cacheable: bool, reason: str).
        """
        if not query or len(query.strip()) < 5:
            return False, "Query quá ngắn"

        q_lower = query.strip().lower()

        # 1. Kiểm tra cờ cấp cứu & từ khóa triệu chứng nguy hiểm
        if is_emergency or any(k in q_lower for k in EMERGENCY_RED_FLAGS):
            return False, "Câu hỏi chứa triệu chứng cấp cứu/nguy kịch (Red Flag) - Bắt buộc Live Reasoning"

        # 2. Kiểm tra câu hỏi nhật ký/cá nhân
        if any(k in q_lower for k in PERSONAL_DATA_KEYWORDS):
            return False, "Câu hỏi truy vấn hoặc ghi nhận dữ liệu cá nhân của bé"

        return True, "Hợp lệ để cache"

    @classmethod
    def generate_cache_key(cls, query: str, age_bracket: str = "general", domain: str = "medical_qa") -> str:
        """Tạo Cache Key chuẩn hóa có phân vùng nhóm tuổi và domain."""
        normalized = " ".join(query.strip().lower().split())
        query_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
        return f"agent_resp:{domain}:{age_bracket}:{query_hash}"

    @classmethod
    async def get_cached_response(
        cls,
        query: str,
        baby_age_months: Optional[int] = None,
        domain: str = "medical_qa"
    ) -> Optional[Dict[str, Any]]:
        """
        Lấy câu trả lời từ Response Cache (L1 Memory -> L2 Redis Cloud).
        """
        cacheable, _ = cls.is_cacheable(query)
        if not cacheable:
            return None

        age_bracket = cls.get_age_bracket(baby_age_months)
        cache_key = cls.generate_cache_key(query, age_bracket=age_bracket, domain=domain)
        now = time.time()

        # 1. Kiểm tra L1 In-Memory LRU Cache (< 1ms)
        if cache_key in cls._l1_cache:
            resp_data, expire_at = cls._l1_cache[cache_key]
            if expire_at > 0 and now > expire_at:
                del cls._l1_cache[cache_key]
            else:
                cls._l1_cache.move_to_end(cache_key)
                cls._l1_hits += 1
                return resp_data

        # 2. Kiểm tra L2 Redis Cloud Cache (~15ms)
        try:
            redis_data = await run_in_threadpool(cache_redis.get_json, cache_key)
            if redis_data and isinstance(redis_data, dict):
                # Đồng bộ ngược vào L1 LRU Cache
                cls._set_l1(cache_key, redis_data, cls._default_ttl)
                cls._l2_hits += 1
                return redis_data
        except Exception as e:
            logger.warning(f"[AgentResponseCacheManager] Lỗi đọc Redis: {e}")

        cls._misses += 1
        return None

    @classmethod
    def _set_l1(cls, key: str, value: Dict[str, Any], ttl_seconds: int):
        """Lưu vào bộ nhớ đệm L1 LRU."""
        expire_at = time.time() + ttl_seconds if ttl_seconds > 0 else 0.0
        if key in cls._l1_cache:
            cls._l1_cache.move_to_end(key)
        elif len(cls._l1_cache) >= cls._l1_max_entries:
            cls._l1_cache.popitem(last=False)
        cls._l1_cache[key] = (value, expire_at)

    @classmethod
    async def set_cached_response(
        cls,
        query: str,
        response_data: Dict[str, Any],
        baby_age_months: Optional[int] = None,
        domain: str = "medical_qa",
        ttl_seconds: Optional[int] = None
    ) -> None:
        """
        Lưu câu trả lời vào Response Cache (đồng bộ cả L1 Memory và L2 Redis Cloud).
        """
        cacheable, _ = cls.is_cacheable(query)
        if not cacheable or not response_data:
            return

        ttl = ttl_seconds if ttl_seconds is not None else cls._default_ttl
        age_bracket = cls.get_age_bracket(baby_age_months)
        cache_key = cls.generate_cache_key(query, age_bracket=age_bracket, domain=domain)

        # 1. Lưu vào L1 In-Memory LRU
        cls._set_l1(cache_key, response_data, ttl)

        # 2. Lưu vào L2 Redis Cloud (Non-blocking qua threadpool)
        try:
            await run_in_threadpool(cache_redis.set_json, cache_key, response_data, ttl)
        except Exception as e:
            logger.warning(f"[AgentResponseCacheManager] Lỗi ghi Redis: {e}")

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """Thống kê chi tiết chỉ số L1/L2 hits, misses và tổng hit rate."""
        total_hits = cls._l1_hits + cls._l2_hits
        total_ops = total_hits + cls._misses
        hit_rate = round((total_hits / total_ops * 100), 2) if total_ops > 0 else 0.0
        return {
            "l1_hits": cls._l1_hits,
            "l2_hits": cls._l2_hits,
            "total_hits": total_hits,
            "misses": cls._misses,
            "hit_rate_pct": hit_rate,
            "l1_size": len(cls._l1_cache),
            "l1_max_entries": cls._l1_max_entries
        }

    @classmethod
    def delete(cls, query: str, baby_age_months: Optional[int] = None, domain: str = "medical_qa"):
        """Xóa 1 key cụ thể khỏi cả L1 và L2 Redis."""
        age_bracket = cls.get_age_bracket(baby_age_months)
        cache_key = cls.generate_cache_key(query, age_bracket=age_bracket, domain=domain)
        if cache_key in cls._l1_cache:
            del cls._l1_cache[cache_key]
        try:
            cache_redis.delete(cache_key)
        except Exception:
            pass

    @classmethod
    def clear(cls):
        """Xóa sạch cache đệm L1 và reset đếm chỉ số."""
        cls._l1_cache.clear()
        cls._l1_hits = 0
        cls._l2_hits = 0
        cls._misses = 0

