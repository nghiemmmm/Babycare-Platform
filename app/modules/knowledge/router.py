"""
Medical Knowledge & PDF Ingestion API Router
Provides endpoints to upload PDF documents, trigger automated ingestion, and list indexed documents.
"""
from typing import List
from fastapi import APIRouter, File, UploadFile, status, Depends
from app.modules.knowledge.schemas import DocumentIngestResponse, DocumentListItem
from app.modules.knowledge.service import KnowledgeIngestionService

router = APIRouter(prefix="/knowledge", tags=["Knowledge & PDF Ingestion"])
_service = KnowledgeIngestionService()


@router.post(
    "/upload-pdf",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên tài liệu PDF và tự động chạy quy trình Ingestion (Parsing, Chunking, Vector Indexing)"
)
async def upload_and_ingest_pdf(
    file: UploadFile = File(...)
):
    """
    Quy trình tự động hóa:
    - Bóc tách trang từ PDF
    - Phân đoạn Sentence-aware Chunking
    - Tạo Vector Embedding (BGE-M3)
    - Nạp vào FAISS Vector Index & BM25 Sparse Index
    """
    return await _service.ingest_pdf(file)


@router.get(
    "/documents",
    response_model=List[DocumentListItem],
    summary="Lấy danh sách các tài liệu tri thức y khoa đã được nạp (Indexed) vào hệ thống"
)
def list_knowledge_documents():
    return _service.list_documents()


@router.delete(
    "/documents/{doc_id}",
    summary="Xóa tài liệu khỏi cơ sở tri thức"
)
def delete_knowledge_document(doc_id: str):
    success = _service.delete_document(doc_id)
    return {"success": success, "message": "Đã xóa tài liệu khỏi hệ thống"}
