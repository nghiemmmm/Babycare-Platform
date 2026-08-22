import os
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from airflow.shared.data_models.models import DocumentStatus, PipelineRunStatus
from airflow.shared.parsing.chunker import SlidingWindowChunker
from airflow.shared.parsing.pdf_parser import PageContent
from airflow.shared.storage.database import engine, init_db, session_scope
from airflow.shared.storage.models import ChunkModel, DocumentModel, PipelineRunModel
from airflow.shared.indexing.vector_indexer import VectorIndexer, load_chunks_as_documents
from langchain_community.embeddings import FakeEmbeddings
from langchain_community.vectorstores import FAISS


class TestEndToEndRAGIngestion(unittest.TestCase):
    """
    Kiểm thử toàn trình:
    Upload Document ➔ Chunker ➔ SQLite Storage ➔ Vector Indexing (FAISS) ➔ RAG Retrieval.
    """

    def setUp(self):
        # Thiết lập test SQLite DB trong thư mục tạm
        self.temp_dir = tempfile.TemporaryDirectory()
        self.faiss_dir = Path(self.temp_dir.name) / "test_faiss_index"

        os.environ["FAISS_INDEX_DIR"] = str(self.faiss_dir)

        # Khởi tạo schema trong database hiện tại
        init_db()

    def tearDown(self):
        try:
            engine.dispose()
        except Exception:
            pass
        try:
            self.temp_dir.cleanup()
        except Exception:
            pass

    def test_full_pipeline_ingestion_and_retrieval(self):
        # 1. Giả lập Task 1: Upload và lưu Document vào bảng 'documents'
        with session_scope() as session:
            # Dọn dẹp test cũ nếu có
            session.query(ChunkModel).delete()
            session.query(PipelineRunModel).delete()
            session.query(DocumentModel).delete()

            doc = DocumentModel(
                filename="cam_nang_cham_soc_tre_so_sinh_who.pdf",
                file_path="/mock/uploads/cam_nang_cham_soc_tre_so_sinh_who.pdf",
                content_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                file_size=102400,
                mime_type="application/pdf",
                status=DocumentStatus.PENDING,
            )
            session.add(doc)
            session.commit()
            doc_id = doc.id

        self.assertIsNotNone(doc_id)

        # 2. Giả lập Task 2 & 3: Parse PDF và Sliding Window Chunking
        sample_pages = [
            PageContent(
                page_number=1,
                text="Tài liệu dinh dưỡng nhi khoa WHO: Trẻ từ 6 tháng tuổi bắt đầu bước vào giai đoạn ăn dặm. "
                     "Nên cho trẻ ăn từ thức ăn lỏng đến đặc, bắt đầu bằng ngũ cốc, rau củ quả nghiền nhuyễn. "
                     "Không nên nêm thêm muối hoặc đường vào khẩu phần ăn của bé dưới 1 tuổi.",
                char_count=260,
                word_count=45,
                is_blank=False,
            ),
            PageContent(
                page_number=2,
                text="Hướng dẫn xử trí sốt ở trẻ nhỏ: Khi thân nhiệt của bé đo ở nách đạt từ 38.5 độ C trở lên, "
                     "phụ huynh có thể sử dụng Paracetamol (Hapacol) liều 10-15mg/kg cân nặng mỗi 4-6 giờ. "
                     "Luôn cho trẻ mặc quần áo thoáng mát và uống nhiều nước.",
                char_count=245,
                word_count=42,
                is_blank=False,
            ),
        ]

        chunker = SlidingWindowChunker(chunk_size=200, chunk_overlap=30)
        chunks = chunker.chunk_pages(sample_pages)
        self.assertGreater(len(chunks), 0)

        # 3. Giả lập Task 4 & 5: Lưu Chunks vào bảng 'chunks' và đánh dấu COMPLETED
        with session_scope() as session:
            doc_in_db = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            doc_in_db.status = DocumentStatus.COMPLETED

            chunk_objs = [
                ChunkModel(
                    document_id=doc_id,
                    chunk_index=c.chunk_index,
                    text=c.text,
                    content_hash=c.content_hash,
                    page_number=c.page_number,
                    token_count=c.token_count,
                )
                for c in chunks
            ]
            session.bulk_save_objects(chunk_objs)

            run_record = PipelineRunModel(
                pipeline_type="airflow",
                run_id="manual__test_run_001",
                status=PipelineRunStatus.COMPLETED,
                documents_processed=1,
                chunks_created=len(chunks),
                embeddings_created=0,
            )
            session.add(run_record)
            session.commit()

        # 4. Giả lập Task 6: Vector Indexing vào FAISS
        langchain_docs = load_chunks_as_documents(doc_ids=[doc_id])
        self.assertEqual(len(langchain_docs), len(chunks))

        # Sử dụng FakeEmbeddings để test logic indexing nhanh
        indexer = VectorIndexer(index_dir=str(self.faiss_dir), embeddings=FakeEmbeddings(size=1024))

        indexed_count = indexer.index_documents(langchain_docs)
        self.assertEqual(indexed_count, len(chunks))
        self.assertTrue((self.faiss_dir / "index.faiss").exists())
        self.assertTrue((self.faiss_dir / "index.pkl").exists())

        # 5. Kiểm tra truy vấn RAG và trích dẫn (Citations)
        loaded_vector_store = FAISS.load_local(
            folder_path=str(self.faiss_dir),
            embeddings=indexer.embeddings,
            allow_dangerous_deserialization=True
        )

        results = loaded_vector_store.similarity_search("ăn dặm cho trẻ 6 tháng", k=2)
        self.assertGreater(len(results), 0)
        
        # Kiểm tra metadata bảo toàn đúng số trang và tên file gốc
        top_match = results[0]
        self.assertIn("source", top_match.metadata)
        self.assertEqual(top_match.metadata["source"], "cam_nang_cham_soc_tre_so_sinh_who.pdf")
        self.assertIn("page", top_match.metadata)
        self.assertIn(top_match.metadata["page"], [1, 2])


if __name__ == "__main__":
    unittest.main()
