import logging
from typing import List
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
from app.AI_agents.core.constant import RERANKER_MODEL_NAME, MODEL_CACHE_DIR

logger = logging.getLogger(__name__)

_cross_encoder_singleton = None


def _get_cross_encoder():
    global _cross_encoder_singleton
    if _cross_encoder_singleton is None:
        try:
            _cross_encoder_singleton = CrossEncoder(
                RERANKER_MODEL_NAME,
                device="cpu",
                cache_folder=MODEL_CACHE_DIR,
                local_files_only=True
            )
        except Exception:
            try:
                _cross_encoder_singleton = CrossEncoder(
                    RERANKER_MODEL_NAME,
                    device="cpu",
                    cache_folder=MODEL_CACHE_DIR
                )
            except Exception as e:
                logger.warning(f"[LocalReranker] Không thể tải CrossEncoder model, sử dụng RRF ranking trực tiếp: {e}")
                _cross_encoder_singleton = "DISABLED"
    return None if _cross_encoder_singleton == "DISABLED" else _cross_encoder_singleton

class LocalReranker:
    def __init__(self):
        self.model = _get_cross_encoder()

    def rerank(self, query: str, documents: list[Document], top_k: int = 3) -> list[Document]:
        """
        Reranks candidate documents using CrossEncoder or fast RRF pass-through.
        """
        if not documents:
            return []
        if self.model is None:
            return documents[:top_k]


        # Tối ưu CPU Latency: Chỉ rerank 6 candidates hàng đầu từ RRF
        candidates = documents[:6]

        # Cắt ngắn văn bản xuống 350 ký tự đầu để giảm độ phức tạp Transformer từ O(1500^2) xuống O(150^2) (~100x nhanh hơn)
        pairs = [[query, doc.page_content[:350]] for doc in candidates]
        
        # Predict relevance scores dưới torch.inference_mode để tối ưu CPU performance
        try:
            import torch
            with torch.inference_mode():
                scores = self.model.predict(pairs, show_progress_bar=False)
        except Exception:
            scores = self.model.predict(pairs, show_progress_bar=False)
        
        # Pair documents with their scores
        scored_docs = list(zip(scores, candidates))
        
        # Sort by score in descending order
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        reranked = [doc for _, doc in scored_docs]
        if len(documents) > 6:
            reranked.extend(documents[6:])

        return reranked[:top_k]
