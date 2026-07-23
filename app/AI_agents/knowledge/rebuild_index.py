"""
Rebuild FAISS Index Script

Xoá index FAISS cũ (nếu có) và build lại từ toàn bộ tài liệu trong documents/.
Chạy sau mỗi lần thêm/sửa tài liệu hoặc đổi chunk size/embedding.

Usage: python -m app.AI_agents.knowledge.rebuild_index
"""
import shutil
from collections import Counter
from pathlib import Path

INDEX_DIR = Path("app/ai/models/faiss_index")


def main():
    if INDEX_DIR.exists():
        shutil.rmtree(INDEX_DIR)
        print(f"Đã xoá index cũ tại {INDEX_DIR}")

    from app.AI_agents.knowledge.document_loader import DocumentLoader
    from app.AI_agents.knowledge.text_splitter import TextSplitter

    loader = DocumentLoader()
    docs = loader.load()
    print(f"Đã nạp {len(docs)} document (theo trang/tệp) từ documents/")

    domain_counts = Counter(d.metadata.get("domain", "unknown") for d in docs)
    for domain, count in sorted(domain_counts.items()):
        print(f"  - domain={domain}: {count} document")

    splitter = TextSplitter()
    chunks = splitter.split_documents(docs)
    print(f"Đã chia thành {len(chunks)} chunk (chunk_size={splitter.chunk_size}, "
          f"chunk_overlap={splitter.chunk_overlap})")

    chunk_domain_counts = Counter(c.metadata.get("domain", "unknown") for c in chunks)
    for domain, count in sorted(chunk_domain_counts.items()):
        print(f"  - domain={domain}: {count} chunk")

    # Import RAGPipeline sau cùng để build/lưu index thật (gọi Gemini embedding API cho từng chunk).
    from app.AI_agents.knowledge.rag_pipeline import RAGPipeline
    print("Đang build FAISS index (gọi Gemini Embedding API cho từng chunk)...")
    RAGPipeline()
    print(f"Hoàn tất. Index đã lưu tại {INDEX_DIR}")


if __name__ == "__main__":
    main()
