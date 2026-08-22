import logging
import sys

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_logger(name: str = "rag_pipeline", level: int = logging.INFO) -> logging.Logger:
    """
    Tạo và cấu hình logger có cấu trúc nhất quán cho hệ thống RAG & Ingestion.

    Args:
        name: Tên của module gọi log.
        level: Ngưỡng log level (mặc định INFO).

    Returns:
        Đối tượng logging.Logger đã được định dạng.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
