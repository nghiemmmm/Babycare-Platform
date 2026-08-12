from sentence_transformers import CrossEncoder
from app.AI_agents.core.constant import RERANKER_MODEL_NAME, MODEL_CACHE_DIR
from langchain_core.documents import Document

_cross_encoder_singleton = None

def _get_cross_encoder():
    global _cross_encoder_singleton
    if _cross_encoder_singleton is None:
        _cross_encoder_singleton = CrossEncoder(
            RERANKER_MODEL_NAME,
            device="cpu",
            cache_folder=MODEL_CACHE_DIR
        )
    return _cross_encoder_singleton

class LocalReranker:
    def __init__(self):
        # Dùng singleton model — load 1 lần vào RAM, reuse mọi request
        self.model = _get_cross_encoder()

    def rerank(self, query: str, documents: list[Document], top_k: int = 3) -> list[Document]:
        """
        Reranks a list of candidate documents using the CrossEncoder model.
        Returns the top_k most relevant documents.
        """
        if not documents:
            return []

        # Construct pairs: (query, document_text)
        pairs = [[query, doc.page_content] for doc in documents]
        
        # Predict relevance scores dưới torch.inference_mode để tối ưu CPU performance
        try:
            import torch
            with torch.inference_mode():
                scores = self.model.predict(pairs, show_progress_bar=False)
        except Exception:
            scores = self.model.predict(pairs, show_progress_bar=False)
        
        # Pair documents with their scores
        scored_docs = list(zip(scores, documents))
        
        # Sort by score in descending order
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k documents
        return [doc for _, doc in scored_docs[:top_k]]
