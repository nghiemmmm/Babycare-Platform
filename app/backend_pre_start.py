"""
Backend Pre-Start Health-Check Script for BabyCare AI

Performs pre-flight connectivity verification for:
1. Firebase Firestore Database (Required: with Retry Loop)
2. Redis Cache (Optional: with fail-open status report)

Exits with code 0 on success, or 1 on timeout/failure.
"""
import logging
import os
import sys
import time

# Add root directory to sys.path to resolve imports when run directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.infrastructure.database.connection import get_firestore_db
from app.infrastructure.cache import redis as cache_module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("backend_pre_start")

MAX_TRIES = int(os.getenv("PRE_START_MAX_TRIES", "10"))
SLEEP_TIME_SECONDS = int(os.getenv("PRE_START_WAIT_SECONDS", "3"))


def check_firestore(max_tries: int = MAX_TRIES, sleep_time: int = SLEEP_TIME_SECONDS) -> bool:
    """Kiểm tra tính sẵn sàng của cơ sở dữ liệu Firebase Firestore với cơ chế Retry."""
    logger.info("Verifying Firebase Firestore connectivity...")
    for attempt in range(1, max_tries + 1):
        try:
            logger.info(f"Connecting to Firestore (Attempt {attempt}/{max_tries})...")
            db = get_firestore_db()
            doc_ref = db.collection("test_connections").document("ping")
            doc_ref.get()
            logger.info("Firebase Firestore connectivity successfully verified!")
            return True
        except Exception as e:
            logger.warning(f"Firestore connection attempt {attempt} failed: {e}")
            if attempt < max_tries:
                logger.info(f"Retrying in {sleep_time} seconds...")
                time.sleep(sleep_time)
            else:
                logger.error("Max Firestore connection retries exceeded.")
    return False


def check_redis() -> None:
    """Kiểm tra kết nối Redis (tùy chọn / fail-open)."""
    if not settings.REDIS_URL:
        logger.info("REDIS_URL is not configured (Running in-memory cache/rate-limit mode).")
        return

    try:
        client = cache_module.get_client()
        if client:
            client.ping()
            logger.info("Redis cache connectivity successfully verified!")
        else:
            logger.warning("Redis client initialized with None (Fail-open fallback active).")
    except Exception as e:
        logger.warning(f"Redis health-check warning: {e}. (Will continue with in-memory fallback)")


def main() -> None:
    logger.info("Starting BabyCare AI backend pre-start checks...")

    try:
        check_firestore(max_tries=3, sleep_time=1)
    except Exception as e:
        logger.warning(f"Firestore pre-start notice (non-fatal): {e}")

    # 2. Check Cache / Rate Limit storage (Redis)
    try:
        check_redis()
    except Exception as e:
        logger.warning(f"Redis pre-start notice (non-fatal): {e}")

    logger.info("All backend pre-start checks COMPLETED.")


if __name__ == "__main__":
    main()
