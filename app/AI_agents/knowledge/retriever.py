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
            source = doc.metadata.get("source", "Tài liệu Y tế")
            chapter = doc.metadata.get("chapter")
            section = doc.metadata.get("section")
            subsection = doc.metadata.get("subsection")
            page = doc.metadata.get("page")
            
            header_parts = [f"Tài liệu {i} (Nguồn: {source}"]
            if page:
                header_parts[0] += f", Trang: {page}"
            header_parts[0] += ")"
            
            if chapter:
                header_parts.append(f"Chương: {chapter}")
            if section:
                header_parts.append(f"Mục: {section}")
            if subsection:
                header_parts.append(f"Tiểu mục: {subsection}")
                
            header = " | ".join(header_parts)
            
            # Prioritize original_text for clean LLM response generation
            body_text = doc.metadata.get("original_text") or doc.page_content
            context_items.append(f"{header}:\n{body_text.strip()}")
            
        return "\n\n".join(context_items)
