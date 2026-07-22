from sentence_transformers import CrossEncoder
from app.AI_agents.core.constant import RERANKER_MODEL_NAME, MODEL_CACHE_DIR
from langchain_core.documents import Document

class LocalReranker:
    def __init__(self):
        # Load CrossEncoder model from local cache directory
        self.model = CrossEncoder(
            RERANKER_MODEL_NAME,
            device="cpu",
            cache_folder=MODEL_CACHE_DIR
        )

    def rerank(self, query: str, documents: list[Document], top_k: int = 3) -> list[Document]:
        """
        Reranks a list of candidate documents using the CrossEncoder model.
        Returns the top_k most relevant documents.
        """
        if not documents:
            return []

        # Construct pairs: (query, document_text)
        pairs = [[query, doc.page_content] for doc in documents]
        
        # Predict relevance scores
        scores = self.model.predict(pairs)
        
        # Pair documents with their scores
        scored_docs = list(zip(scores, documents))
        
        # Sort by score in descending order
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Return top_k documents
        return [doc for _, doc in scored_docs[:top_k]]
