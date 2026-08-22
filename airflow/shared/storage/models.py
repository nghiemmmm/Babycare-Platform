from datetime import datetime
from sqlalchemy import (
    BigInteger,
    CHAR,
    Column,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from airflow.shared.data_models.models import DocumentStatus, PipelineRunStatus
from airflow.shared.storage.database import Base


# ===========================================================================
# 1. Bảng documents
# ===========================================================================
class DocumentModel(Base):
    """
    Bảng lưu trữ thông tin các tập tin tài liệu đã nạp vào hệ thống.
    """
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(1024), nullable=False)
    content_hash = Column(CHAR(64), nullable=False, unique=True, index=True)
    file_size = Column(BigInteger, nullable=False, default=0)
    mime_type = Column(String(100), nullable=False, default="application/pdf")
    status = Column(
        SAEnum(DocumentStatus, name="document_status_enum", native_enum=False),
        nullable=False,
        default=DocumentStatus.PENDING,
        index=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    chunks = relationship("ChunkModel", back_populates="document", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DocumentModel(id={self.id}, filename='{self.filename}', status='{self.status}')>"


# ===========================================================================
# 2. Bảng chunks
# ===========================================================================
class ChunkModel(Base):
    """
    Bảng lưu trữ các đoạn văn bản (chunks) sau khi phân đoạn qua Sliding Window Chunker.
    """
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    content_hash = Column(CHAR(64), nullable=False, index=True)
    page_number = Column(Integer, nullable=True)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    document = relationship("DocumentModel", back_populates="chunks")

    __table_args__ = (
        Index("idx_doc_chunk_order", "document_id", "chunk_index"),
    )

    def __repr__(self) -> str:
        return f"<ChunkModel(id={self.id}, doc_id={self.document_id}, index={self.chunk_index})>"


# ===========================================================================
# 3. Bảng pipeline_runs
# ===========================================================================
class PipelineRunModel(Base):
    """
    Bảng theo dõi số liệu và lịch sử thực thi của từng phiên chạy Airflow Pipeline.
    """
    __tablename__ = "pipeline_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pipeline_type = Column(String(100), nullable=False, default="airflow")
    run_id = Column(String(255), nullable=False, unique=True, index=True)
    status = Column(
        SAEnum(PipelineRunStatus, name="pipeline_run_status_enum", native_enum=False),
        nullable=False,
        default=PipelineRunStatus.RUNNING,
        index=True,
    )
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    documents_processed = Column(Integer, nullable=False, default=0)
    chunks_created = Column(Integer, nullable=False, default=0)
    embeddings_created = Column(Integer, nullable=False, default=0)
    run_metadata = Column(JSON, nullable=True, default=dict)

    def __repr__(self) -> str:
        return f"<PipelineRunModel(id={self.id}, run_id='{self.run_id}', status='{self.status}')>"
