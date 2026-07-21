from app.AI_agents.knowledge.rag_pipeline import RAGPipeline

class MedicalRetriever:
    def __init__(self):
        self.pipeline = RAGPipeline()

    def retrieve_context(self, query: str, k: int = 3, metadata_filter: dict = None) -> str:
        """
        Retrieves context for Q&A and formats it as a single string.
        """
        docs = self.pipeline.retrieve(query, k=k, metadata_filter=metadata_filter)
        if not docs:
            return "Không tìm thấy tài liệu y tế phù hợp."
        
        context_items = []
        for i, doc in enumerate(docs, 1):
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page")
            page_str = f", Trang: {page}" if page else ""
            context_items.append(f"Tài liệu {i} (Nguồn: {source}{page_str}):\n{doc.page_content}")
            
        return "\n\n".join(context_items)
