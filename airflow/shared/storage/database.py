import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker, Session

logger = logging.getLogger("database")

Base = declarative_base()

# Cấu hình đường dẫn SQLite Database mặc định
# Môi trường Docker: /opt/airflow/data/rag_app.db
# Môi trường Local: ./rag_app.db
DEFAULT_SQLITE_PATH = os.getenv("SQLITE_DB_PATH", "/opt/airflow/data/rag_app.db")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DEFAULT_SQLITE_PATH}")


def _enable_sqlite_wal(dbapi_con, con_record):
    """Bật WAL mode (Write-Ahead Logging) và busy_timeout để SQLite hỗ trợ đa luồng/tiến trình ghi mà không bị khóa."""
    cursor = dbapi_con.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA busy_timeout=10000;")  # Chờ tối đa 10s nếu DB đang bận
    cursor.close()


def get_engine():
    """Khởi tạo SQLAlchemy engine cho SQLite (hoặc PostgreSQL nếu cấu hình lại qua env)."""
    db_url = os.getenv("DATABASE_URL", DATABASE_URL)
    
    if db_url.startswith("sqlite"):
        # Tự động tạo thư mục chứa file SQLite nếu chưa có
        file_path_str = db_url.replace("sqlite:///", "")
        if file_path_str and file_path_str != ":memory:":
            db_dir = Path(file_path_str).parent
            db_dir.mkdir(parents=True, exist_ok=True)

        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False, "timeout": 30},
            echo=False
        )
        event.listen(engine, "connect", _enable_sqlite_wal)
        return engine

    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False
    )


# Singleton Engine & Session Factory
engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Khởi tạo schema tất cả các bảng vào SQLite Database."""
    from airflow.shared.storage.models import DocumentModel, ChunkModel, PipelineRunModel  # noqa
    Base.metadata.create_all(bind=engine)
    logger.info(f"[Database] Đã khởi tạo schema SQLite thành công tại: {DATABASE_URL}")


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Context manager cung cấp transactional scope cho Airflow tasks:
    - Tự động commit khi thành công
    - Tự động rollback khi có lỗi
    - Luôn đóng session giải phóng tài nguyên
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"[Database] Transaction rollback: {e}")
        raise
    finally:
        session.close()


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency injection cung cấp session cho các endpoint REST API.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()