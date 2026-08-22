import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from airflow.shared.data_models.models import (
    DocumentResponse,
    DocumentStatus,
    ChunkResponse,
)
from airflow.shared.storage.database import get_session, init_db
from airflow.shared.storage.models import DocumentModel, ChunkModel
from airflow.shared.utils.hashing import compute_file_sha256
from airflow.shared.utils.logging import get_logger

logger = get_logger("ingestion_service")

# Đường dẫn thư mục Shared Volume dùng chung giữa FastAPI Service và Airflow
UPLOAD_DIR_PATH = os.getenv("UPLOAD_DIR", "/tmp/ml_orchestration/uploads")
UPLOAD_DIR = Path(UPLOAD_DIR_PATH)

app = FastAPI(
    title="Document Ingestion Service",
    description="REST API để tiếp nhận tập tin PDF, kiểm tra mã băm trùng lặp SHA-256, lưu vào shared volume và ghi nhận trạng thái PENDING.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Khởi tạo thư mục shared volume và schema cơ sở dữ liệu khi khởi động."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    try:
        init_db()
        logger.info(f"[IngestionService] Shared Volume sẵn sàng tại: {UPLOAD_DIR}")
    except Exception as e:
        logger.warning(f"[IngestionService] Cảnh báo kết nối Database khi khởi động: {e}")


@app.get("/health", summary="Kiểm tra trạng thái dịch vụ Ingestion")
def health_check():
    return {
        "status": "healthy",
        "service": "ingestion_service",
        "upload_dir": str(UPLOAD_DIR)
    }


# ===========================================================================
# Endpoint chính: Upload PDF Document
# Thực hiện đúng 3 thao tác cốt lõi:
# 1. Tính mã băm SHA-256 để phát hiện trùng lặp
# 2. Lưu file vào Shared Volume mà Airflow có thể truy cập
# 3. Ghi nhận record vào bảng documents với status = PENDING (không xử lý đồng bộ)
# ===========================================================================
@app.post(
    "/documents",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Tải lên tài liệu PDF mới",
)
async def upload_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    """
    Tiếp nhận tập tin PDF tải lên:
    - Tính SHA-256 phát hiện trùng lặp
    - Lưu file vào Shared Volume
    - Ghi nhận trạng thái PENDING cho Airflow xử lý nền
    """
    logger.info(f"[Upload] Nhận yêu cầu tải lên tập tin: {file.filename}")

    # 1. Kiểm tra định dạng PDF
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hệ thống hiện tại chỉ hỗ trợ tập tin định dạng .pdf"
        )

    # 2. Lưu tạm file vào Shared Volume
    file_timestamp = int(datetime.utcnow().timestamp())
    saved_file_path = UPLOAD_DIR / f"{file_timestamp}_{file.filename}"

    try:
        with open(saved_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = saved_file_path.stat().st_size

        # 3. Tính mã băm SHA-256 của tập tin
        content_hash = compute_file_sha256(str(saved_file_path))

        # 4. Kiểm tra trùng lặp trong cơ sở dữ liệu
        existing_doc = session.query(DocumentModel).filter(
            DocumentModel.content_hash == content_hash
        ).first()

        if existing_doc:
            logger.warning(f"[Upload] Phát hiện tập tin trùng mã SHA-256: {content_hash} (Doc ID: {existing_doc.id})")
            if saved_file_path.exists():
                saved_file_path.unlink()
            
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Tập tin đã tồn tại trong hệ thống với ID: {existing_doc.id}"
            )

        # 5. Tạo mới Document record với trạng thái PENDING
        document = DocumentModel(
            filename=file.filename,
            file_path=str(saved_file_path),
            content_hash=content_hash,
            file_size=file_size,
            mime_type="application/pdf",
            status=DocumentStatus.PENDING,
        )

        session.add(document)
        session.commit()
        session.refresh(document)

        logger.info(f"[Upload] Đã lưu tài liệu thành công: ID {document.id}, status=PENDING")

        return DocumentResponse(
            id=document.id,
            filename=document.filename,
            file_path=document.file_path,
            content_hash=document.content_hash,
            file_size=document.file_size,
            mime_type=document.mime_type,
            status=document.status,
            created_at=document.created_at,
            updated_at=document.updated_at,
            chunks_count=0,
        )

    except HTTPException:
        raise
    except Exception as e:
        if saved_file_path.exists():
            saved_file_path.unlink()
        logger.error(f"[Upload] Lỗi khi xử lý tải lên: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Không thể tải lên tập tin: {str(e)}"
        )


@app.get(
    "/documents/{document_id}",
    response_model=DocumentResponse,
    summary="Kiểm tra trạng thái xử lý của tài liệu",
)
def get_document_status(document_id: int, session: Session = Depends(get_session)):
    doc = session.query(DocumentModel).filter(DocumentModel.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Không tìm thấy tài liệu.")

    chunks_count = session.query(ChunkModel).filter(ChunkModel.document_id == document_id).count()
    return DocumentResponse(
        id=doc.id,
        filename=doc.filename,
        file_path=doc.file_path,
        content_hash=doc.content_hash,
        file_size=doc.file_size,
        mime_type=doc.mime_type,
        status=doc.status,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        chunks_count=chunks_count,
    )


@app.get(
    "/documents/{document_id}/chunks",
    response_model=List[ChunkResponse],
    summary="Lấy danh sách các chunks sau khi Airflow xử lý",
)
def get_document_chunks(document_id: int, session: Session = Depends(get_session)):
    chunks = session.query(ChunkModel).filter(
        ChunkModel.document_id == document_id
    ).order_by(ChunkModel.chunk_index).all()
    return chunks