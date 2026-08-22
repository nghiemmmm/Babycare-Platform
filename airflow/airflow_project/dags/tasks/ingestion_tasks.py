import os
import time
from datetime import datetime
from typing import Any, Dict, List

from airflow.shared.data_models.models import DocumentStatus, PipelineRunStatus
from airflow.shared.parsing.chunker import SlidingWindowChunker
from airflow.shared.parsing.pdf_parser import PDFParser, parse_pdf
from airflow.shared.storage.database import session_scope
from airflow.shared.storage.models import ChunkModel, DocumentModel, PipelineRunModel
from airflow.shared.utils.file_io import read_data_from_file, write_data_to_file
from airflow.shared.utils.logging import get_logger

logger = get_logger("ingestion_tasks")


# ===========================================================================
# Task 1: Fetch Pending Documents
# ===========================================================================
def fetch_pending_documents(**context) -> List[int]:
    """
    Task 1: Fetch documents that need processing.
    Ghi danh sách document IDs ra file trung gian và truyền filepath qua XCom (Claim-Check pattern).
    """
    logger.info("Fetching pending documents...")
    with session_scope() as session:
        pending_docs = session.query(DocumentModel).filter(
            DocumentModel.status == DocumentStatus.PENDING
        ).all()
        doc_ids = [doc.id for doc in pending_docs]

    logger.info(f"Found {len(doc_ids)} pending documents: {doc_ids}")

    # Lấy run_id từ context
    dag_run = context.get("dag_run")
    run_id = dag_run.run_id if dag_run else f"run_{int(time.time())}"

    # Ghi dữ liệu ra file trung gian trên Shared Volume
    filepath = write_data_to_file(doc_ids, f"{run_id}_document_ids.json")
    context["task_instance"].xcom_push(key="document_ids_file", value=filepath)

    return doc_ids


# ===========================================================================
# Task 2: Parse Documents
# ===========================================================================
def parse_documents(**context) -> Dict[str, int]:
    """
    Task 2: Parse PDF documents into pages.
    Reads document IDs from previous task and parses each PDF.
    """
    logger.info("Parsing documents...")
    ti = context["task_instance"]
    doc_ids_file = ti.xcom_pull(task_ids="fetch_documents", key="document_ids_file")
    
    if not doc_ids_file or not os.path.exists(doc_ids_file):
        logger.info("[Task 2 - Parse] Không có file document_ids.")
        return {"parsed": 0}

    doc_ids = read_data_from_file(doc_ids_file)
    dag_run = context.get("dag_run")
    run_id = dag_run.run_id if dag_run else f"run_{int(time.time())}"
    
    parsed_count = 0
    parsed_manifest = []

    with session_scope() as session:
        for doc_id in doc_ids:
            pages_filename = f"{run_id}_doc_{doc_id}_pages.json"
            
            doc = session.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
            if not doc:
                logger.warning(f"Document {doc_id} not found")
                continue

            try:
                pages = parse_pdf(doc.file_path)
                logger.info(f"Parsed {len(pages)} pages from {doc.filename}")
                pages_file = write_data_to_file(pages, pages_filename)
                parsed_count += 1
                parsed_manifest.append({
                    "id": doc.id,
                    "filename": doc.filename,
                    "file_path": doc.file_path,
                    "pages_file": pages_file,
                    "total_pages": len(pages),
                    "start_time": time.time(),
                })
            except Exception as e:
                logger.error(f"Failed to parse document {doc_id}: {str(e)}")
                doc.status = DocumentStatus.FAILED
                session.commit()

    # Ghi manifest parsed docs để task sau xử lý
    manifest_file = write_data_to_file(parsed_manifest, f"{run_id}_parsed_docs.json")
    ti.xcom_push(key="parsed_docs_file", value=manifest_file)

    logger.info(f"Successfully parsed {parsed_count} documents")
    return {"parsed": parsed_count}


# ===========================================================================
# Task 3: Split Text into Overlapping Chunks (Sliding Window)
# ===========================================================================
def chunk_documents(**context) -> str:
    """
    Task 3: Đọc file parsed pages từ Task 2, phân đoạn Sliding Window (500 chars / 50 overlap).
    Lưu các ChunkModel vào SQLite Database và ghi kết quả raw chunks ra file trung gian.
    """
    ti = context["task_instance"]
    parsed_docs_file = ti.xcom_pull(task_ids="parse_documents", key="parsed_docs_file")
    
    if not parsed_docs_file or not os.path.exists(parsed_docs_file):
        return ""

    parsed_docs = read_data_from_file(parsed_docs_file)
    if not parsed_docs:
        return ""

    chunker = SlidingWindowChunker(chunk_size=500, chunk_overlap=50)
    chunked_results = []

    with session_scope() as session:
        for doc_info in parsed_docs:
            if doc_info.get("parse_error"):
                chunked_results.append(doc_info)
                continue

            doc_id = doc_info.get("id")
            pages = doc_info.get("pages")
            if not pages and doc_info.get("pages_file") and os.path.exists(doc_info["pages_file"]):
                pages = read_data_from_file(doc_info["pages_file"])

            raw_chunks = []
            chunk_models = []
            current_chunk_idx = 0

            for page in (pages or []):
                if page.get("is_blank"):
                    continue
                page_chunks = chunker.chunk_text(
                    text=page.get("text", ""),
                    page_number=page.get("page_number"),
                    start_index=current_chunk_idx,
                )
                for c in page_chunks:
                    raw_chunks.append({
                        "chunk_index": c.chunk_index,
                        "page_number": c.page_number,
                        "text": c.text,
                        "content_hash": c.content_hash,
                        "token_count": c.token_count,
                    })
                    if doc_id is not None:
                        chunk_models.append(
                            ChunkModel(
                                document_id=doc_id,
                                chunk_index=c.chunk_index,
                                text=c.text,
                                content_hash=c.content_hash,
                                page_number=c.page_number,
                                token_count=c.token_count,
                            )
                        )
                current_chunk_idx += len(page_chunks)

            # Lưu Chunks vào SQLite Database (Xóa chunk cũ nếu có trước khi insert mới)
            if doc_id is not None and chunk_models:
                session.query(ChunkModel).filter(ChunkModel.document_id == doc_id).delete()
                session.bulk_save_objects(chunk_models)
                session.flush()

            doc_info["raw_chunks"] = raw_chunks
            logger.info(f"[Task 3/5 - Chunk] Doc ID {doc_id}: Đã tạo và lưu {len(raw_chunks)} chunks vào Database.")
            chunked_results.append(doc_info)

    dag_run = context.get("dag_run")
    run_id = dag_run.run_id if dag_run else f"run_{int(time.time())}"
    filepath = write_data_to_file(chunked_results, f"{run_id}_chunked_docs.json")
    ti.xcom_push(key="chunked_docs_file", value=filepath)
    return filepath


# ===========================================================================
# Task 4: Validate Chunks
# ===========================================================================
def validate_chunks(**context) -> Dict[str, int]:
    """
    Task 4: Validate chunk quality.
    Checks for empty chunks, excessive length, etc.
    """
    logger.info("Validating chunks...")
    ti = context["task_instance"]
    doc_ids_file = ti.xcom_pull(task_ids="fetch_documents", key="document_ids_file")
    
    if not doc_ids_file or not os.path.exists(doc_ids_file):
        return {"valid": 0, "invalid": 0}

    doc_ids = read_data_from_file(doc_ids_file)
    valid_count = 0
    invalid_count = 0

    with session_scope() as session:
        for doc_id in doc_ids:
            chunks = session.query(ChunkModel).filter(
                ChunkModel.document_id == doc_id
            ).all()

            for chunk in chunks:
                # 1. Too short (ít hơn 50 ký tự)
                if len(chunk.text) < 50:
                    logger.warning(f"Chunk {chunk.id} too short: {len(chunk.text)} chars")
                    invalid_count += 1
                    continue

                # 2. Too long (nhiều hơn 2000 ký tự)
                if len(chunk.text) > 2000:
                    logger.warning(f"Chunk {chunk.id} too long: {len(chunk.text)} chars")
                    invalid_count += 1
                    continue

                # 3. Empty or whitespace only
                if not chunk.text.strip():
                    logger.warning(f"Chunk {chunk.id} is empty or whitespace only")
                    invalid_count += 1
                    continue

                valid_count += 1

    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid chunks")
    return {"valid": valid_count, "invalid": invalid_count}


# ===========================================================================
# Task 5: Mark Complete
# ===========================================================================
def mark_documents_complete(**context) -> Dict[str, int]:
    """
    Task 5: Mark documents as complete.
    Updates document status and creates pipeline run record.
    """
    logger.info("Marking documents complete...")
    ti = context["task_instance"]
    doc_ids_file = ti.xcom_pull(
        key="document_ids_file",
        task_ids="fetch_documents"
    )
    
    if not doc_ids_file or not os.path.exists(doc_ids_file):
        logger.info("[Task 5 - Complete] Không có file document_ids.")
        return {"documents_completed": 0}

    doc_ids = read_data_from_file(doc_ids_file)

    with session_scope() as session:
        for doc_id in doc_ids:
            doc = session.query(DocumentModel).filter(
                DocumentModel.id == doc_id
            ).first()
            if doc and doc.status in (DocumentStatus.PROCESSING, DocumentStatus.PENDING):
                doc.status = DocumentStatus.COMPLETED

        # Đếm chính xác tổng số chunks đã tạo cho các tài liệu này
        total_chunks = session.query(ChunkModel).filter(
            ChunkModel.document_id.in_(doc_ids)
        ).count() if doc_ids else 0

        dag_run = context.get("dag_run")
        run_id = dag_run.run_id if dag_run else f"run_{int(time.time())}"
        started_at = getattr(dag_run, "start_date", datetime.utcnow()) or datetime.utcnow()
        execution_date = context.get("execution_date", datetime.utcnow())

        pipeline_run = PipelineRunModel(
            pipeline_type="airflow",
            run_id=run_id,
            status=PipelineRunStatus.COMPLETED,
            started_at=started_at,
            completed_at=datetime.utcnow(),
            documents_processed=len(doc_ids),
            chunks_created=total_chunks,
            embeddings_created=0,
            run_metadata={
                "dag_id": context["dag"].dag_id,
                "execution_date": str(execution_date)
            }
        )
        session.add(pipeline_run)
        session.commit()

        logger.info(f"Pipeline run {run_id} completed: {len(doc_ids)} docs, {total_chunks} chunks")
        return {"documents_completed": len(doc_ids)}


# ===========================================================================
# Task 6: Generate Embeddings & Index into FAISS
# ===========================================================================
def index_embeddings(**context) -> Dict[str, int]:
    """
    Task 6: Tự động nhúng vector các chunks mới bằng mô hình BGE-M3
    và đẩy vào FAISS Vector Index (app/ai/models/faiss_index/).
    Cập nhật metrics embeddings_created vào bảng pipeline_runs.
    """
    logger.info("Starting BGE-M3 Vector Embedding & FAISS Indexing...")
    ti = context["task_instance"]
    doc_ids_file = ti.xcom_pull(
        key="document_ids_file",
        task_ids="fetch_documents"
    )
    
    if not doc_ids_file or not os.path.exists(doc_ids_file):
        logger.info("[Task 6 - Embed] Không có file document_ids.")
        return {"embeddings_created": 0}

    doc_ids = read_data_from_file(doc_ids_file)
    if not doc_ids:
        return {"embeddings_created": 0}

    try:
        from airflow.shared.indexing.vector_indexer import index_documents_into_faiss
        embedded_count = index_documents_into_faiss(doc_ids=doc_ids)
    except Exception as e:
        logger.error(f"[Task 6 - Embed] Lỗi khi tạo vector embeddings: {e}")
        embedded_count = 0

    # Cập nhật số lượng embeddings_created vào bảng pipeline_runs
    dag_run = context.get("dag_run")
    run_id = dag_run.run_id if dag_run else None

    if run_id:
        with session_scope() as session:
            run_record = session.query(PipelineRunModel).filter(
                PipelineRunModel.run_id == run_id
            ).first()
            if run_record:
                run_record.embeddings_created = embedded_count
                session.commit()

    logger.info(f"FAISS Indexing complete: {embedded_count} vector embeddings created.")
    return {"embeddings_created": embedded_count}
