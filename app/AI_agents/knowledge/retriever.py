from typing import Optional
from app.AI_agents.knowledge.rag_pipeline import RAGPipeline

class MedicalRetriever:
    def __init__(self):
        self.pipeline = RAGPipeline()

    def retrieve_context(self, query: str, k: int = 3, domain: Optional[str] = None, metadata_filter: Optional[dict] = None) -> str:
        """
        Retrieves context for Q&A and formats it as a single string.
        """
        docs = self.pipeline.retrieve(query, k=k, domain=domain)
        if not docs and metadata_filter:
            # Fallback to unfiltered retrieve if metadata filter returned no results
            docs = self.pipeline.retrieve(query, k=k, domain=None)
        
        if not docs:
            return "Không tìm thấy tài liệu y tế phù hợp."
        
        context_items = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            context_items.append(f"Tài liệu {i} (Nguồn: {source}):\n{doc.page_content}")
            
        return "\n\n".join(context_items)
