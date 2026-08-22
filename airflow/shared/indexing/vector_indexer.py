import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from airflow.shared.data_models.models import DocumentStatus
from airflow.shared.storage.database import session_scope
from airflow.shared.storage.models import ChunkModel, DocumentModel, PipelineRunModel
from airflow.shared.utils.logging import get_logger

logger = get_logger("vector_indexer")

# Đường dẫn mặc định tới thư mục lưu FAISS index
DEFAULT_FAISS_INDEX_DIR = os.getenv(
    "FAISS_INDEX_DIR",
    str(Path(__file__).resolve().parent.parent.parent.parent / "app" / "ai" / "models" / "faiss_index")
)


def get_rag_embeddings():
    """
    Lấy embedding model chuẩn của hệ thống BabyCare AI:
    Ưu tiên BGE-M3 local (1024 chiều) từ app.AI_agents.memory.embeddings.
    """
    try:
        from app.AI_agents.memory.embeddings import get_embeddings
        return get_embeddings()
    except Exception as e:
        logger.warning(f"[VectorIndexer] Không thể nạp BGE-M3 từ app.AI_agents ({e}), sử dụng FakeEmbeddings dự phòng.")
        from langchain_community.embeddings import FakeEmbeddings
        return FakeEmbeddings(size=1024)


def load_chunks_as_documents(doc_ids: Optional[List[int]] = None) -> List[Document]:
    """
    Đọc các chunks từ bảng SQLite 'chunks' và chuyển thành LangChain Document
    kèm đầy đủ metadata (source, page, chunk_index, content_hash) phục vụ trích dẫn.

    Args:
        doc_ids: Danh sách document_id cần lấy (nếu None sẽ lấy tất cả tài liệu COMPLETED).

    Returns:
        Danh sách LangChain Document.
    """
    langchain_docs: List[Document] = []

    with session_scope() as session:
        query = session.query(DocumentModel).filter(
            DocumentModel.status.in_([DocumentStatus.COMPLETED, DocumentStatus.PROCESSING])
        )
        if doc_ids:
            query = query.filter(DocumentModel.id.in_(doc_ids))

        documents = query.all()
        for doc in documents:
            for chunk in doc.chunks:
                langchain_docs.append(Document(
                    page_content=chunk.text,
                    metadata={
                        "source": doc.filename,
                        "page": chunk.page_number or 1,
                        "chunk_index": chunk.chunk_index,
                        "content_hash": chunk.content_hash,
                        "document_id": doc.id,
                        "domain": "pediatrics",
                    }
                ))

    logger.info(f"[VectorIndexer] Đã load {len(langchain_docs)} chunks từ SQLite thành LangChain Documents.")
    return langchain_docs


class VectorIndexer:
    """
    Cầu nối vector hóa: Đọc Chunks từ SQLite ➔ BGE-M3 Embeddings ➔ Lưu vào FAISS Index.
    """

    def __init__(self, index_dir: Optional[str] = None, embeddings: Optional[Any] = None):
        self.index_dir = Path(index_dir or DEFAULT_FAISS_INDEX_DIR)
        self.embeddings = embeddings if embeddings is not None else get_rag_embeddings()

    def index_documents(self, documents: List[Document], batch_size: int = 64) -> int:
        """
        Nhúng và lưu danh sách Document vào FAISS Index (hỗ trợ incremental update).

        Args:
            documents: Danh sách LangChain Document.
            batch_size: Số lượng chunk nhúng mỗi batch.

        Returns:
            Tổng số vectors đã được nhúng và lưu vào FAISS.
        """
        if not documents:
            logger.info("[VectorIndexer] Không có tài liệu nào để nhúng vào FAISS.")
            return 0

        logger.info(f"[VectorIndexer] Bắt đầu nhúng {len(documents)} chunks vào FAISS ({self.index_dir})...")

        vector_store = None
        # Kiểm tra xem đã có index cũ hay chưa để nạp nối tiếp (Incremental Update)
        if self.index_dir.exists() and (self.index_dir / "index.faiss").exists():
            try:
                vector_store = FAISS.load_local(
                    folder_path=str(self.index_dir),
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                logger.info(f"[VectorIndexer] Đã nạp FAISS index hiện có ({vector_store.index.ntotal} vectors).")
            except Exception as e:
                logger.warning(f"[VectorIndexer] Không thể nạp FAISS index cũ ({e}), tiến hành tạo mới.")
                vector_store = None

        total_batches = (len(documents) + batch_size - 1) // batch_size
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            batch_num = i // batch_size + 1
            logger.info(f"[VectorIndexer] Đang xử lý batch {batch_num}/{total_batches} ({len(batch)} chunks)...")

            if vector_store is None:
                vector_store = FAISS.from_documents(batch, self.embeddings)
            else:
                vector_store.add_documents(batch)

        # Lưu lại FAISS index xuống đĩa
        if vector_store:
            self.index_dir.mkdir(parents=True, exist_ok=True)
            vector_store.save_local(str(self.index_dir))
            total_vectors = vector_store.index.ntotal
            logger.info(f"[VectorIndexer] Đã lưu FAISS index thành công tại: {self.index_dir} (Tổng: {total_vectors} vectors)")
            return len(documents)

        return 0


def index_documents_into_faiss(
    doc_ids: Optional[List[int]] = None,
    index_dir: Optional[str] = None,
    embeddings: Optional[Any] = None,
) -> int:
    """
    Tiện ích một chạm: Đọc chunks của doc_ids từ SQLite ➔ Nhúng BGE-M3 ➔ Lưu vào FAISS Store.
    """
    documents = load_chunks_as_documents(doc_ids=doc_ids)
    if not documents:
        return 0

    indexer = VectorIndexer(index_dir=index_dir, embeddings=embeddings)
    return indexer.index_documents(documents)
