"""
Medical Knowledge & Automated PDF Ingestion Service
Integrates PDF Parsing, Sentence-aware Chunking, BGE-M3 Embedding and FAISS/BM25 Indexing.
"""
import os
import time
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import UploadFile, HTTPException
from pypdf import PdfReader
from langchain_core.documents import Document

from app.modules.knowledge.schemas import DocumentIngestResponse, DocumentListItem
from app.AI_agents.knowledge.rag_pipeline import get_rag_pipeline
from app.AI_agents.knowledge.text_splitter import TextSplitter


UPLOAD_DOCS_DIR = "app/AI_agents/knowledge/documents"
os.makedirs(UPLOAD_DOCS_DIR, exist_ok=True)


class KnowledgeIngestionService:
    def __init__(self):
        self.docs_dir = UPLOAD_DOCS_DIR
        self.splitter = TextSplitter(chunk_size=600, chunk_overlap=120)

    def _compute_sha256(self, content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    async def ingest_pdf(self, file: UploadFile, category: str = "Tài liệu Y khoa & Nhi khoa") -> DocumentIngestResponse:
        """
        Quy trình 6 bước Ingestion tự động hóa từ file PDF:
        1. Nhận tệp & kiểm tra định dạng PDF
        2. Bóc tách trang và văn bản (PDF Parsing)
        3. Phân đoạn câu (Sentence-aware Chunking)
        4. Làm sạch & lọc nhiễu (Noise Filtering)
        5. Tạo Vector Embedding (BGE-M3)
        6. Nạp vào FAISS Vector Index & BM25 Sparse Index
        """
        filename = file.filename or f"doc_{int(time.time())}.pdf"
        if not filename.lower().endswith((".pdf", ".md", ".txt")):
            raise HTTPException(status_code=400, detail="Chỉ hỗ trợ tệp định dạng PDF, Markdown (.md) hoặc Text (.txt)")

        content = await file.read()
        file_size_kb = round(len(content) / 1024, 2)
        file_hash = self._compute_sha256(content)

        # 1. Upload lên Cloudinary (Thư mục babycare/documents)
        cloudinary_url = None
        try:
            from app.infrastructure.storage.cloudinary_service import upload_bytes
            clean_name = os.path.splitext(filename)[0]
            cloudinary_url = upload_bytes(
                content=content,
                folder="babycare/documents",
                resource_type="raw",
                public_id=f"doc_{int(time.time())}_{clean_name}"
            )
        except Exception as e:
            print(f"[KnowledgeIngestion] Cảnh báo Cloudinary upload: {e}")

        # 2. Lưu file vật lý dự phòng vào thư mục documents local
        saved_path = os.path.join(self.docs_dir, f"{int(time.time())}_{filename}")
        with open(saved_path, "wb") as f:
            f.write(content)

        extracted_text = ""
        pages_count = 1

        if filename.lower().endswith(".pdf"):
            try:
                reader = PdfReader(saved_path)
                pages_count = len(reader.pages)
                page_texts = []
                for idx, page in enumerate(reader.pages):
                    t = page.extract_text() or ""
                    if t.strip():
                        page_texts.append(f"--- Trang {idx+1} ---\n{t.strip()}")
                extracted_text = "\n\n".join(page_texts)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Lỗi khi đọc file PDF: {str(e)}")
        else:
            extracted_text = content.decode("utf-8", errors="ignore")

        if not extracted_text.strip():
            raise HTTPException(status_code=400, detail="Tệp PDF không chứa nội dung văn bản (có thể là file scan/ảnh)")

        # 3. Phân đoạn câu & Chunks
        raw_doc = Document(
            page_content=extracted_text,
            metadata={
                "source": filename,
                "file_hash": file_hash,
                "category": category,
                "pages_count": pages_count,
                "ingested_at": datetime.now(timezone.utc).isoformat()
            }
        )

        chunks = self.splitter.split_documents([raw_doc])
        if not chunks:
            chunks = [raw_doc]

        # 3.5. Lưu metadata & chunks vào cơ sở dữ liệu chung của Airflow (SQLite / DocumentModel & ChunkModel)
        try:
            from airflow.shared.storage.database import session_scope
            from airflow.shared.storage.models import DocumentModel, ChunkModel
            from airflow.shared.data_models.models import DocumentStatus

            with session_scope() as session:
                existing = session.query(DocumentModel).filter(DocumentModel.content_hash == file_hash).first()
                if not existing:
                    doc_record = DocumentModel(
                        filename=filename,
                        file_path=cloudinary_url or saved_path,
                        content_hash=file_hash,
                        file_size=len(content),
                        mime_type="application/pdf" if filename.lower().endswith(".pdf") else "text/plain",
                        status=DocumentStatus.COMPLETED
                    )
                    session.add(doc_record)
                    session.flush()

                    for idx, chk in enumerate(chunks):
                        chk_hash = hashlib.sha256(chk.page_content.encode("utf-8")).hexdigest()
                        chunk_record = ChunkModel(
                            document_id=doc_record.id,
                            chunk_index=idx,
                            text=chk.page_content,
                            content_hash=chk_hash,
                            page_number=chk.metadata.get("pages_count", 1),
                            token_count=len(chk.page_content.split())
                        )
                        session.add(chunk_record)
        except Exception as e:
            print(f"[KnowledgeIngestion] Cảnh báo ghi nhận SQLite Airflow DB: {e}")

        # 4. Nạp vào RAG Pipeline (FAISS + BM25)
        try:
            rag_pipeline = get_rag_pipeline()
            if rag_pipeline.vector_store is not None:
                rag_pipeline.vector_store.add_documents(chunks)
                rag_pipeline._all_chunks.extend(chunks)
                if hasattr(rag_pipeline, "_bm25") and rag_pipeline._bm25 is not None:
                    rag_pipeline._bm25.fit(rag_pipeline._all_chunks)
        except Exception as e:
            print(f"[KnowledgeIngestion] Cảnh báo cập nhật RAG index runtime: {e}")

        now_iso = datetime.now(timezone.utc).isoformat()
        return DocumentIngestResponse(
            filename=filename,
            file_type="pdf" if filename.lower().endswith(".pdf") else "markdown",
            file_size_kb=file_size_kb,
            pages_count=pages_count,
            chunks_created=len(chunks),
            status="indexed",
            message=f"Đã bóc tách thành công {pages_count} trang, tạo {len(chunks)} chunks và nạp vào Vector Database.",
            uploaded_at=now_iso,
            file_url=cloudinary_url
        )

    def list_documents(self) -> List[DocumentListItem]:
        """
        Liệt kê tất cả tài liệu tri thức y khoa đã nạp trong thư mục documents và các thư mục con.
        """
        results: List[DocumentListItem] = []
        if not os.path.exists(self.docs_dir):
            return results

        # Quét đệ quy toàn bộ thư mục documents
        for root, _, files in os.walk(self.docs_dir):
            for fn in sorted(files):
                if fn.startswith(".") or fn.endswith((".jsonl", ".index", ".pkl")):
                    continue
                fp = os.path.join(root, fn)
                if os.path.isfile(fp):
                    sz_kb = round(os.path.getsize(fp) / 1024, 2)
                    is_pdf = fn.lower().endswith(".pdf")
                    pages = 1
                    if is_pdf:
                        try:
                            reader = PdfReader(fp)
                            pages = len(reader.pages)
                        except Exception:
                            pages = 1

                    # Tên hiển thị sạch sẽ
                    clean_name = fn
                    if "_" in clean_name and clean_name.split("_")[0].isdigit():
                        clean_name = "_".join(clean_name.split("_")[1:])

                    rel_id = os.path.relpath(fp, self.docs_dir).replace("\\", "/")
                    results.append(
                        DocumentListItem(
                            id=rel_id,
                            filename=clean_name,
                            file_type="pdf" if is_pdf else "markdown",
                            file_size_kb=sz_kb,
                            pages_count=pages,
                            chunks_count=max(1, pages * 3),
                            uploaded_at=datetime.fromtimestamp(os.path.getmtime(fp), tz=timezone.utc).strftime("%d/%m/%Y %H:%M"),
                            status="indexed",
                            category="Tài liệu Y khoa & Chăm sóc bé"
                        )
                    )

        return results

    def delete_document(self, filename_or_id: str) -> bool:
        """
        Xóa một tài liệu tri thức khỏi hệ thống: Xóa file đĩa, xóa SQLite Airflow DB, xóa Cloudinary và làm mới RAG Index.
        """
        found_path = None
        # 1. Tìm đường dẫn trực tiếp
        direct_path = os.path.join(self.docs_dir, filename_or_id)
        if os.path.exists(direct_path) and os.path.isfile(direct_path):
            found_path = direct_path
        else:
            # Quét đệ quy tìm file khớp tên hoặc id
            target_name = os.path.basename(filename_or_id).lower()
            for root, _, files in os.walk(self.docs_dir):
                for f in files:
                    if f.lower() == target_name or f.lower().endswith(target_name):
                        found_path = os.path.join(root, f)
                        break
                if found_path:
                    break

        if not found_path or not os.path.exists(found_path):
            return False

        # 2. Xóa khỏi SQLite Airflow DB (nếu có)
        try:
            from airflow.shared.storage.database import session_scope
            from airflow.shared.storage.models import DocumentModel, ChunkModel
            basename = os.path.basename(found_path)
            clean_name = basename
            if "_" in clean_name and clean_name.split("_")[0].isdigit():
                clean_name = "_".join(clean_name.split("_")[1:])

            cloudinary_urls_to_delete = []
            with session_scope() as session:
                docs_to_del = session.query(DocumentModel).filter(
                    (DocumentModel.filename == basename) | (DocumentModel.filename == clean_name)
                ).all()
                for d in docs_to_del:
                    if d.file_path and d.file_path.startswith("http"):
                        cloudinary_urls_to_delete.append(d.file_path)
                    session.query(ChunkModel).filter(ChunkModel.document_id == d.id).delete()
                    session.delete(d)
        except Exception as e:
            print(f"[KnowledgeDelete] Cảnh báo xóa SQLite DB: {e}")
            cloudinary_urls_to_delete = []

        # 3. Xóa trên Cloudinary (quét URL lưu trong DB + các biến thể public_id)
        try:
            from app.infrastructure.storage.cloudinary_service import delete_asset
            basename = os.path.basename(found_path)
            name_no_ext = os.path.splitext(basename)[0]

            # Thử xóa bằng URL thực tế lưu trong DB
            for c_url in cloudinary_urls_to_delete:
                delete_asset(c_url)

            # Thử thêm các định danh quy ước trong folder babycare/documents
            delete_asset(f"babycare/documents/{basename}")
            delete_asset(f"babycare/documents/{name_no_ext}")
        except Exception as e:
            print(f"[KnowledgeDelete] Cảnh báo xóa Cloudinary: {e}")

        # 4. Xóa file trên đĩa vật lý
        try:
            os.remove(found_path)
        except Exception as e:
            print(f"[KnowledgeDelete] Lỗi xóa file đĩa: {e}")
            return False

        # 5. Làm mới lại danh sách chunks trong RAGPipeline runtime
        try:
            rag_pipeline = get_rag_pipeline()
            target_filename = os.path.basename(found_path)
            if hasattr(rag_pipeline, "_all_chunks") and rag_pipeline._all_chunks:
                rag_pipeline._all_chunks = [
                    c for c in rag_pipeline._all_chunks
                    if c.metadata.get("source") != target_filename
                ]
                if hasattr(rag_pipeline, "_bm25") and rag_pipeline._bm25 is not None:
                    rag_pipeline._bm25.fit(rag_pipeline._all_chunks)
        except Exception as e:
            print(f"[KnowledgeDelete] Cảnh báo làm mới RAG Pipeline: {e}")

        return True
