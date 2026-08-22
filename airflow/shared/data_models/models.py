import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DocumentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class PipelineRunStatus(str, enum.Enum):
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ---------------------------------------------------------------------------
# 1. Document Schemas (Bảng documents)
# ---------------------------------------------------------------------------
class DocumentBase(BaseModel):
    filename: str = Field(..., description="Tên gốc của file PDF")
    file_path: str = Field(..., description="Đường dẫn tuyệt đối lưu trên đĩa / Shared Volume")
    content_hash: str = Field(..., description="Mã SHA-256 duy nhất của file content")
    file_size: int = Field(..., ge=0, description="Dung lượng file (bytes)")
    mime_type: str = Field(default="application/pdf", description="MIME Type của tập tin")
    status: DocumentStatus = Field(default=DocumentStatus.PENDING, description="Trạng thái xử lý")


class DocumentCreate(DocumentBase):
    pass


class DocumentInDB(DocumentBase):
    id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    content_hash: str
    file_size: int
    mime_type: str
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime
    chunks_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# 2. Chunk Schemas (Bảng chunks)
# ---------------------------------------------------------------------------
class ChunkBase(BaseModel):
    chunk_index: int = Field(..., ge=0, description="Thứ tự chunk trong tài liệu (0, 1, 2...)")
    text: str = Field(..., description="Nội dung văn bản của đoạn chunk")
    content_hash: str = Field(..., description="Mã băm SHA-256 của đoạn văn bản")
    page_number: Optional[int] = Field(default=None, ge=1, description="Trang PDF xuất xứ của chunk")
    token_count: Optional[int] = Field(default=None, ge=0, description="Ước tính số token / word count")


class ChunkCreate(ChunkBase):
    document_id: int = Field(..., description="Khóa ngoại liên kết tới bảng documents")


class ChunkInDB(ChunkBase):
    id: int
    document_id: int
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        from_attributes = True


class ChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    text: str
    content_hash: str
    page_number: Optional[int]
    token_count: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# 3. Pipeline Run Schemas (Bảng pipeline_runs)
# ---------------------------------------------------------------------------
class PipelineRunBase(BaseModel):
    pipeline_type: str = Field(default="airflow", description="Loại pipeline (airflow hoặc argo)")
    run_id: str = Field(..., description="Mã phiên chạy Airflow duy nhất (dag_run.run_id)")
    status: PipelineRunStatus = Field(default=PipelineRunStatus.RUNNING)
    documents_processed: int = Field(default=0, ge=0)
    chunks_created: int = Field(default=0, ge=0)
    embeddings_created: int = Field(default=0, ge=0)
    run_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PipelineRunCreate(PipelineRunBase):
    pass


class PipelineRunInDB(PipelineRunBase):
    id: int
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PipelineRunResponse(BaseModel):
    id: int
    pipeline_type: str
    run_id: str
    status: PipelineRunStatus
    started_at: datetime
    completed_at: Optional[datetime]
    documents_processed: int
    chunks_created: int
    embeddings_created: int
    run_metadata: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True
