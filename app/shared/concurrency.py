"""
Shared Concurrency Module

Bọc fastapi.concurrency.run_in_threadpool bằng asyncio.wait_for để giới hạn
thời gian chờ tối đa cho các call đồng bộ (Firebase Admin SDK / Firestore
SDK) chạy trong threadpool, tránh một request chậm chiếm dụng thread vô
thời hạn và kéo theo cạn kiệt threadpool của toàn bộ app.
"""
import asyncio
import logging
from fastapi.concurrency import run_in_threadpool as _run_in_threadpool
from app.core.config import settings
from app.shared.exceptions import UpstreamTimeoutError

logger = logging.getLogger(__name__)


async def run_in_threadpool(func, *args, **kwargs):
    """Run a blocking call in the threadpool, bounded by THREADPOOL_TIMEOUT_SECONDS."""
    try:
        return await asyncio.wait_for(
            _run_in_threadpool(func, *args, **kwargs),
            timeout=settings.THREADPOOL_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError:
        logger.warning(
            f"Threadpool call {func.__name__} vượt quá {settings.THREADPOOL_TIMEOUT_SECONDS}s"
        )
        raise UpstreamTimeoutError()
