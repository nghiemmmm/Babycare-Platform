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
        print(f"Da xoa index cu tai {INDEX_DIR}", flush=True)

    from app.AI_agents.knowledge.document_loader import DocumentLoader
    from app.AI_agents.knowledge.text_splitter import TextSplitter

    loader = DocumentLoader()
    docs = loader.load()
    print(f"\nTong so documents sau khi load: {len(docs)}")

    # Thống kê theo nguồn file
    source_counts = Counter(d.metadata.get("source", "unknown") for d in docs)
    print("\nThong ke theo file nguon:")
    for source, count in sorted(source_counts.items()):
        print(f"  - {source}: {count} documents")

    # Thống kê theo domain
    domain_counts = Counter(d.metadata.get("domain", "unknown") for d in docs)
    print("\nThong ke theo domain:")
    for domain, count in sorted(domain_counts.items()):
        print(f"  - domain={domain}: {count} documents")

    # JSONL docs đã được pre-chunked sẵn → không split thêm
    # PDF/MD/TXT docs → cần split theo chunk_size
    jsonl_docs = [d for d in docs if d.metadata.get("source", "").endswith(".jsonl")]
    other_docs  = [d for d in docs if not d.metadata.get("source", "").endswith(".jsonl")]

    splitter = TextSplitter()
    split_chunks = splitter.split_documents(other_docs)

    all_chunks = jsonl_docs + split_chunks
    print(f"\nChunks tu JSONL (pre-chunked, khong split): {len(jsonl_docs)}")
    print(f"Chunks tu PDF/MD/TXT (sau khi split):       {len(split_chunks)}")
    print(f"Tong chunks se embed:                        {len(all_chunks)}")

    embeddings = get_embeddings()
    batch_size = 64
    vector_store = None

    print(f"\nDang build FAISS index theo tung batch {batch_size} chunks bang BGE-M3 local...", flush=True)
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
        print(f"\nHoan tat! FAISS index da luu tai {INDEX_DIR}")
        print(f"Tong vectors: {vector_store.index.ntotal}")

if __name__ == "__main__":
    main()


