"""
Async Job Manager Module

Cung cấp cơ chế quản lý trạng thái các tác vụ xử lý bất đồng bộ (Background Jobs)
cho các tính năng AI chạy lâu (như sinh thực đơn 7 ngày, xuất báo cáo PDF y khoa).
Lưu trạng thái job vào Redis Cache (fail-open) và duy trì In-Memory Store fallback.
"""
from enum import Enum
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from app.infrastructure.cache import redis as cache_redis
from app.shared.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

# In-memory fallback dictionary cho các job khi Redis chưa khả dụng
_in_memory_jobs: Dict[str, Dict[str, Any]] = {}
MAX_IN_MEMORY_JOBS = 500


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class JobManager:
    TTL_SECONDS = 3600 * 2  # Lưu trạng thái Job trong 2 giờ

    @classmethod
    def create_job(cls, job_type: str, user_id: str, meta: Optional[dict] = None) -> str:
        """Tạo một job_id mới và khởi tạo trạng thái PENDING."""
        job_id = f"job_{uuid.uuid4().hex[:12]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "user_id": user_id,
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "meta": meta or {},
            "result": None,
            "error": None,
            "created_at": now_iso,
            "updated_at": now_iso
        }

        # 1. Lưu vào In-memory dictionary
        if len(_in_memory_jobs) > MAX_IN_MEMORY_JOBS:
            # Xóa các job cũ nhất nếu vượt quá dung lượng bộ nhớ
            oldest_keys = list(_in_memory_jobs.keys())[:100]
            for k in oldest_keys:
                _in_memory_jobs.pop(k, None)

        _in_memory_jobs[job_id] = job_data

        # 2. Thử lưu vào Redis Cache (async / non-blocking call qua threadpool)
        cache_key = f"async_job:{job_id}"
        try:
            cache_redis.set_json(cache_key, job_data, cls.TTL_SECONDS)
        except Exception as e:
            logger.warning(f"[JobManager] Không thể lưu job '{job_id}' vào Redis: {e}")

        logger.info(f"[JobManager] Đã tạo async job '{job_id}' (Loại: {job_type}, User: {user_id}).")
        return job_id

    @classmethod
    def update_job(
        cls,
        job_id: str,
        status: JobStatus,
        progress: Optional[int] = None,
        result: Optional[dict] = None,
        error: Optional[str] = None
    ) -> None:
        """Cập nhật tiến trình và trạng thái của Job."""
        now_iso = datetime.now(timezone.utc).isoformat()
        job_data = cls.get_job(job_id)

        if not job_data:
            job_data = {
                "job_id": job_id,
                "status": status.value,
                "created_at": now_iso
            }

        job_data["status"] = status.value
        job_data["updated_at"] = now_iso
        if progress is not None:
            job_data["progress"] = progress
        if result is not None:
            job_data["result"] = result
        if error is not None:
            job_data["error"] = error

        # 1. Cập nhật In-memory
        _in_memory_jobs[job_id] = job_data

        # 2. Cập nhật Redis Cache
        cache_key = f"async_job:{job_id}"
        try:
            cache_redis.set_json(cache_key, job_data, cls.TTL_SECONDS)
        except Exception as e:
            logger.warning(f"[JobManager] Lỗi cập nhật Redis job '{job_id}': {e}")

        logger.info(f"[JobManager] Cập nhật job '{job_id}' -> Status: {status.value}")

    @classmethod
    def get_job(cls, job_id: str) -> Optional[dict]:
        """Lấy thông tin và trạng thái hiện tại của Job."""
        # 1. Kiểm tra trong Redis trước
        cache_key = f"async_job:{job_id}"
        cached = cache_redis.get_json(cache_key)
        if cached:
            return cached

        # 2. Fallback kiểm tra trong In-memory
        return _in_memory_jobs.get(job_id)
