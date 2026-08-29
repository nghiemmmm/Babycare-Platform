"""
Knowledge & Document Ingestion Schemas Module
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class DocumentIngestResponse(BaseModel):
    filename: str = Field(..., description="Tên tệp tài liệu")
    file_type: str = Field("pdf", description="Định dạng tệp")
    file_size_kb: float = Field(..., description="Dung lượng tệp (KB)")
    pages_count: int = Field(1, description="Số trang tài liệu")
    chunks_created: int = Field(..., description="Số đoạn văn bản (chunks) được sinh ra")
    status: str = Field("indexed", description="Trạng thái: indexed (đã nạp), processing (đang xử lý), failed (thất bại)")
    message: str = Field(..., description="Thông báo kết quả")
    uploaded_at: str = Field(..., description="Thời điểm tải lên (ISO)")
    file_url: Optional[str] = Field(None, description="Đường dẫn lưu trữ Cloudinary của tài liệu")


class DocumentListItem(BaseModel):
    id: str
    filename: str
    file_type: str = "pdf"
    file_size_kb: float
    pages_count: int
    chunks_count: int
    uploaded_at: str
    status: str = "indexed"
    category: Optional[str] = "Tài liệu Y khoa & Chăm sóc bé"
    file_url: Optional[str] = None
