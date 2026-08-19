from typing import Optional, List
from langchain_core.documents import Document
from app.AI_agents.knowledge.document_loader import DocumentLoader
from app.AI_agents.knowledge.text_splitter import TextSplitter
from langchain_community.vectorstores import FAISS
from app.AI_agents.memory.embeddings import get_embeddings
from app.AI_agents.knowledge.sparse_retriever import SparseBM25Retriever
from app.AI_agents.core.constant import (
    HYBRID_RETRIEVE_CANDIDATES,
    RAG_ENABLE_MMR,
    RAG_MMR_LAMBDA,
    RAG_MMR_FETCH_K_MULTIPLIER
)
from langsmith import traceable


# BM25 candidates và FAISS candidates trước khi rerank
_DENSE_CANDIDATES = HYBRID_RETRIEVE_CANDIDATES   # = 10 (từ constant.py)
_SPARSE_CANDIDATES = HYBRID_RETRIEVE_CANDIDATES  # = 10


def _reciprocal_rank_fusion(
    dense_docs: List[Document],
    sparse_docs: List[Document],
    k: int = 60,
) -> List[Document]:
    """
    Reciprocal Rank Fusion — merge 2 danh sách ranked docs thành 1 danh sách.
    Công thức: RRF_score(d) = sum(1 / (k + rank_i(d)))
    Docs xuất hiện ở cả 2 list và/hoặc ở rank cao sẽ được điểm cao hơn.
    """
    scores: dict[str, float] = {}
    doc_map: dict[str, Document] = {}

    for rank, doc in enumerate(dense_docs, start=1):
        key = doc.page_content[:100]   # dùng 100 ký tự đầu làm key dedup
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        doc_map[key] = doc

    for rank, doc in enumerate(sparse_docs, start=1):
        key = doc.page_content[:100]
        scores[key] = scores.get(key, 0.0) + 1.0 / (k + rank)
        doc_map[key] = doc

    sorted_keys = sorted(scores, key=lambda x: scores[x], reverse=True)
    return [doc_map[key] for key in sorted_keys]


class RAGPipeline:
    """
    Hybrid RAG Pipeline:
      1. FAISS dense retrieval (BGE-M3 embeddings)
      2. BM25 sparse retrieval (keyword matching, tiếng Việt-friendly)
      3. Reciprocal Rank Fusion (merge 2 danh sách)
      4. CrossEncoder reranker (mxbai-rerank-xsmall) → top-k cuối
    """

    def __init__(self):
        self.loader = DocumentLoader()
        self.splitter = TextSplitter()
        self.embeddings = get_embeddings()
        self.vector_store = None
        self._all_chunks: List[Document] = []    # lưu để fit BM25
        self._bm25 = SparseBM25Retriever()
        self._reranker: Optional[LocalReranker] = None
        self._initialize_pipeline()

    def _initialize_pipeline(self):
        """Load FAISS index từ disk (hoặc build mới), rồi fit BM25 trên cùng tập chunks."""
        import os
        index_dir = "app/ai/models/faiss_index"

        if os.path.exists(index_dir):
            try:
                self.vector_store = FAISS.load_local(
                    folder_path=index_dir,
                    embeddings=self.embeddings,
                    allow_dangerous_deserialization=True
                )
                # Lấy lại documents từ FAISS docstore để fit BM25
                self._all_chunks = list(self.vector_store.docstore._dict.values())
            except Exception as e:
                print(f"Không thể tải FAISS index cục bộ, tiến hành dựng lại: {e}")

        if self.vector_store is None:
            docs = self.loader.load()
            chunks = self.splitter.split_documents(docs)
            if chunks:
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
                try:
                    self.vector_store.save_local(index_dir)
                except Exception as e:
                    print(f"Lỗi khi lưu FAISS index cục bộ: {e}")
                self._all_chunks = chunks
            else:
                from langchain_core.documents import Document as Doc
                dummy = Doc(page_content="dummy", metadata={"source": "dummy"})
                self.vector_store = FAISS.from_documents([dummy], self.embeddings)
                self._all_chunks = [dummy]

        # Fit BM25 trên toàn bộ chunks (nhanh, pure Python)
        self._bm25.fit(self._all_chunks)

        # Lazy-load reranker (load CrossEncoder model)
        try:
            self._reranker = LocalReranker()
        except Exception as e:
            print(f"[RAGPipeline] Reranker failed to load (non-fatal, fallback to RRF only): {e}")
            self._reranker = None

    def retrieve(self, query: str, k: int = 3, domain: Optional[str] = None) -> List[Document]:
        """
        Hybrid retrieval: FAISS dense + BM25 sparse → RRF merge → CrossEncoder rerank.

        Args:
            query: Câu hỏi của người dùng
            k: Số kết quả trả về cuối cùng
            domain: Filter theo domain metadata (vd "allergy_safety", "nutrition_general")

        Returns:
            Top-k documents liên quan nhất sau khi rerank.
        """
        if not self.vector_store:
            return []

        filter_dict = {"domain": domain} if domain else None

        from concurrent.futures import ThreadPoolExecutor

        def _do_dense():
            try:
                total_vectors = getattr(self.vector_store.index, "ntotal", 100) if hasattr(self.vector_store, "index") else 100
                fetch_limit = min(total_vectors, _DENSE_CANDIDATES * RAG_MMR_FETCH_K_MULTIPLIER)
                if RAG_ENABLE_MMR and hasattr(self.vector_store, "max_marginal_relevance_search"):
                    try:
                        return self.vector_store.max_marginal_relevance_search(
                            query,
                            k=_DENSE_CANDIDATES,
                            fetch_k=fetch_limit,
                            lambda_mult=RAG_MMR_LAMBDA,
                            filter=filter_dict
                        )
                    except Exception as mmr_err:
                        pass
                
                # Fallback to similarity_search
                if filter_dict:
                    return self.vector_store.similarity_search(
                        query, k=_DENSE_CANDIDATES,
                        filter=filter_dict, fetch_k=fetch_limit
                    )
                else:
                    return self.vector_store.similarity_search(query, k=_DENSE_CANDIDATES)
            except Exception:
                return []

        def _do_sparse():
            try:
                domain_filter = (lambda meta: meta.get("domain") == domain) if domain else None
                return self._bm25.retrieve(
                    query, k=_SPARSE_CANDIDATES, filter_func=domain_filter
                )
            except Exception:
                return []

        dense_docs = _do_dense()
        sparse_docs = _do_sparse()

        # ── 3. Reciprocal Rank Fusion ─────────────────────────────────────────

        merged_docs = _reciprocal_rank_fusion(dense_docs, sparse_docs)

        if not merged_docs:
            return []

        # ── 4. CrossEncoder Reranker ──────────────────────────────────────────
        if self._reranker and len(merged_docs) > k:
            try:
                return self._reranker.rerank(query, merged_docs, top_k=k)
            except Exception as e:
                print(f"[RAGPipeline] Reranker error (fallback to RRF top-k): {e}")

        # Fallback: RRF top-k (nếu reranker lỗi hoặc merged_docs <= k)
        return merged_docs[:k]

    @traceable(name="RAGPipeline.retrieve_with_plan")
    def retrieve_with_plan(self, plan: any, k: int = 3) -> List[Document]:

        """
        Hybrid Retrieval bằng SearchPlan đã được bóc tách từ QueryAnalyzer:
        - BM25 dùng keywords cốt lõi
        - FAISS Dense dùng dense_query đã được chuẩn hóa ngữ nghĩa (kèm MMR đa dạng hóa)
        - Metadata filter dùng plan.filters
        """
        if not self.vector_store:
            return []

        keywords_str = " ".join(plan.keywords) if getattr(plan, "keywords", None) else getattr(plan, "dense_query", "")
        dense_query = getattr(plan, "dense_query", "") or keywords_str
        filters = getattr(plan, "filters", {}) or None

        def _do_dense_plan():
            try:
                total_vectors = getattr(self.vector_store.index, "ntotal", 100) if hasattr(self.vector_store, "index") else 100
                fetch_limit = min(total_vectors, _DENSE_CANDIDATES * RAG_MMR_FETCH_K_MULTIPLIER)
                if RAG_ENABLE_MMR and hasattr(self.vector_store, "max_marginal_relevance_search"):
                    try:
                        return self.vector_store.max_marginal_relevance_search(
                            dense_query,
                            k=_DENSE_CANDIDATES,
                            fetch_k=fetch_limit,
                            lambda_mult=RAG_MMR_LAMBDA,
                            filter=filters
                        )
                    except Exception:
                        pass

                # Fallback to similarity_search
                if filters:
                    return self.vector_store.similarity_search(
                        dense_query, k=_DENSE_CANDIDATES,
                        filter=filters, fetch_k=total_vectors
                    )
                else:
                    return self.vector_store.similarity_search(dense_query, k=_DENSE_CANDIDATES)
            except Exception:
                return []

        def _do_sparse_plan():
            try:
                return self._bm25.retrieve(
                    keywords_str, k=_SPARSE_CANDIDATES
                )
            except Exception:
                return []

        dense_docs = _do_dense_plan()
        sparse_docs = _do_sparse_plan()

        # 3. RRF Fusion
        merged_docs = _reciprocal_rank_fusion(dense_docs, sparse_docs)
        if not merged_docs:
            return []


        # 4. Rerank
        if self._reranker and len(merged_docs) > k:
            try:
                return self._reranker.rerank(dense_query, merged_docs, top_k=k)
            except Exception:
                pass

        return merged_docs[:k]

from app.AI_agents.knowledge.context_compressor import ContextCompressor, compact_and_budget_context





# ---------------------------------------------------------------------------
# Module-level RAGPipeline Singleton
# ---------------------------------------------------------------------------

_rag_pipeline_instance: Optional[RAGPipeline] = None


def get_rag_pipeline() -> RAGPipeline:
    """
    Trả về RAGPipeline singleton dùng chung cho toàn app.
    Tự khởi tạo nếu chưa có (lazy fallback cho CLI / testing).
    Trong FastAPI production: gọi `init_rag_pipeline()` trong lifespan startup.
    """
    global _rag_pipeline_instance
    if _rag_pipeline_instance is None:
        _rag_pipeline_instance = RAGPipeline()
    return _rag_pipeline_instance


def init_rag_pipeline() -> RAGPipeline:
    """
    Khởi tạo RAGPipeline singleton. Gọi 1 lần trong lifespan startup.
    Load FAISS index từ disk vào RAM ngay khi app khởi động.
    """
    global _rag_pipeline_instance
    _rag_pipeline_instance = RAGPipeline()
    return _rag_pipeline_instance


def clear_rag_pipeline() -> None:
    """Giải phóng FAISS vector store khỏi RAM. Gọi trong lifespan shutdown."""
    global _rag_pipeline_instance
    if _rag_pipeline_instance is not None:
        _rag_pipeline_instance.vector_store = None
    _rag_pipeline_instance = None

