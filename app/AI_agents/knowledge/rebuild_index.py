import sys
import time
import shutil
from collections import Counter
from pathlib import Path
from langchain_community.vectorstores import FAISS
from app.AI_agents.memory.embeddings import get_embeddings

# Force UTF-8 encoding for Windows stdout logging
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

INDEX_DIR = Path("app/ai/models/faiss_index")

def main():
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
        print(f"Đã xóa index cũ tại {INDEX_DIR}", flush=True)

    from app.AI_agents.knowledge.document_loader import DocumentLoader
    from app.AI_agents.knowledge.text_splitter import TextSplitter

    # 1. Nạp tài liệu từ thư mục tĩnh (documents/)
    loader = DocumentLoader()
    docs = loader.load()
    print(f"\nTổng số documents tĩnh sau khi load: {len(docs)}")

    source_counts = Counter(d.metadata.get("source", "unknown") for d in docs)
    print("\nThống kê theo file nguồn tĩnh:")
    for source, count in sorted(source_counts.items()):
        print(f"  - {source}: {count} documents")

    # 2. Nạp thêm các chunks đã được Airflow xử lý từ SQLite Database
    airflow_chunks = []
    try:
        from airflow.shared.indexing.vector_indexer import load_chunks_as_documents
        airflow_chunks = load_chunks_as_documents()
        print(f"\nĐã nạp {len(airflow_chunks)} chunks từ Airflow SQLite Database")
    except Exception as e:
        print(f"\nKhông thể nạp SQLite Chunks từ Airflow (bỏ qua): {e}")

    # JSONL docs đã được pre-chunked sẵn → không split thêm
    jsonl_docs = [d for d in docs if d.metadata.get("source", "").endswith(".jsonl")]
    other_docs  = [d for d in docs if not d.metadata.get("source", "").endswith(".jsonl")]

    splitter = TextSplitter()
    split_chunks = splitter.split_documents(other_docs)

    # Hợp nhất toàn bộ: JSONL + Split Chunks + Airflow Chunks
    all_chunks = jsonl_docs + split_chunks + airflow_chunks
    print(f"\nChunks từ JSONL (pre-chunked):              {len(jsonl_docs)}")
    print(f"Chunks từ PDF/MD/TXT tĩnh (sau khi split):    {len(split_chunks)}")
    print(f"Chunks từ Airflow SQLite Database:            {len(airflow_chunks)}")
    print(f"Tổng số chunks sẽ embed vào FAISS:            {len(all_chunks)}")

    embeddings = get_embeddings()
    batch_size = 64
    vector_store = None

    print(f"\nĐang build FAISS index theo từng batch {batch_size} chunks bằng BGE-M3 local...", flush=True)
    total_batches = (len(all_chunks) + batch_size - 1) // batch_size
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i:i + batch_size]
        batch_num = i // batch_size + 1
        print(f"  --> Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)...", flush=True)
        if vector_store is None:
            vector_store = FAISS.from_documents(batch, embeddings)
        else:
            vector_store.add_documents(batch)
        print(f"  --> Done batch {batch_num}/{total_batches}", flush=True)

    if vector_store:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        vector_store.save_local(str(INDEX_DIR))
        print(f"\nHoàn tất! FAISS index đã lưu tại: {INDEX_DIR}")
        print(f"Tổng số vectors: {vector_store.index.ntotal}")

if __name__ == "__main__":
    main()
