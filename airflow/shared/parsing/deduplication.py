from typing import List, Set, Tuple
from sqlalchemy.orm import Session
from airflow.shared.data_models.models import DocumentStatus
from airflow.shared.parsing.chunker import TextChunk
from airflow.shared.storage.models import DocumentModel, ChunkModel
from airflow.shared.utils.logging import get_logger

logger = get_logger("deduplication")


class DeduplicationService:
    """
    Dịch vụ kiểm tra và loại bỏ trùng lặp ở cả cấp độ Document (file hash) và Chunk (content hash).
    """

    @staticmethod
    def is_document_duplicate(db: Session, file_hash: str) -> Tuple[bool, DocumentModel | None]:
        """
        Kiểm tra xem file_hash đã từng được lưu và xử lý thành công trong cơ sở dữ liệu hay chưa.

        Args:
            db: SQLAlchemy Session.
            file_hash: Mã SHA-256 của file.

        Returns:
            Tuple (is_duplicate, existing_document_model_or_none).
        """
        doc = db.query(DocumentModel).filter(DocumentModel.content_hash == file_hash).first()
        if doc and doc.status in (DocumentStatus.COMPLETED, DocumentStatus.PENDING, DocumentStatus.PROCESSING):
            logger.info(f"[Deduplication] Phát hiện tài liệu trùng lặp (ID: {doc.id}, Status: {doc.status})")
            return True, doc
        return False, doc

    @staticmethod
    def filter_duplicate_chunks(chunks: List[TextChunk]) -> List[TextChunk]:
        """
        Loại bỏ các chunk có nội dung trùng lặp (dựa trên content_hash) ngay trong cùng một tài liệu.

        Args:
            chunks: Danh sách TextChunk.

        Returns:
            Danh sách TextChunk đã lọc trùng.
        """
        seen_hashes: Set[str] = set()
        unique_chunks: List[TextChunk] = []

        for chunk in chunks:
            if chunk.content_hash not in seen_hashes:
                seen_hashes.add(chunk.content_hash)
                unique_chunks.append(chunk)

        if len(unique_chunks) < len(chunks):
            logger.info(f"[Deduplication] Đã lọc bỏ {len(chunks) - len(unique_chunks)} chunks trùng lặp.")

        return unique_chunks
