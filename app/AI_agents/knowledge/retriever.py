from typing import Optional
from app.AI_agents.knowledge.rag_pipeline import get_rag_pipeline, compact_and_budget_context
from app.AI_agents.knowledge.query_analyzer import QueryAnalyzer, SearchPlan

_RAG_RESULT_CACHE: dict[str, str] = {}

class MedicalRetriever:
    def __init__(self):
        # Dùng singleton RAGPipeline — không tạo FAISS instance mới
        self.pipeline = get_rag_pipeline()
        self.analyzer = QueryAnalyzer()

    async def retrieve_context_with_plan(
        self,
        query: str,
        k: int = 3,
        domain: Optional[str] = None,
        max_tokens: int = 800
    ) -> str:
        """
        Xử lý Ambiguous Request bằng Query Understanding ➔ SearchPlan ➔ Planned Hybrid Search ➔ Context Compaction & Token Budget.
        """
        cache_key = f"{query.strip().lower()}_{k}_{domain}_{max_tokens}"
        if cache_key in _RAG_RESULT_CACHE:
            return _RAG_RESULT_CACHE[cache_key]
        # 1. Query Understanding bằng Gemini Flash (Free)
        plan: SearchPlan = await self.analyzer.analyze(query, domain_hint=domain)

        # 2. Planned Hybrid Retrieval (Run in threadpool to prevent CPU/RAG blocking on asyncio loop)
        from app.shared.concurrency import run_in_threadpool
        docs = await run_in_threadpool(self.pipeline.retrieve_with_plan, plan, k)

        if not docs:
            # Fallback nếu dùng plan không ra docs
            docs = await run_in_threadpool(self.pipeline.retrieve, query, k, domain)


        # 3 & 4. Context Compaction + Token Budget
        compacted = compact_and_budget_context(docs, plan=plan, max_tokens=max_tokens)
        if len(_RAG_RESULT_CACHE) > 500:
            _RAG_RESULT_CACHE.clear()
        _RAG_RESULT_CACHE[cache_key] = compacted
        return compacted

    def retrieve_context(
        self,
        query: str,
        k: int = 3,
        domain: Optional[str] = None,
        metadata_filter: Optional[dict] = None
    ) -> str:
        """
        Retrieves context for Q&A and formats it as a single formatted string.
        Supports both direct domain parameter and metadata_filter dict mapping.
        """
        target_domain = domain
        if not target_domain and metadata_filter:
            category = metadata_filter.get("category")
            if category == "nutrition":
                target_domain = "nutrition_general"
            elif category == "health":
                target_domain = "illness_diet"

        docs = []
        if target_domain:
            docs = self.pipeline.retrieve(query, k=k, domain=target_domain)

        if not docs:
            docs = self.pipeline.retrieve(query, k=k, domain=None)
        
        if not docs:
            return "Không tìm thấy tài liệu y tế phù hợp."
        
        return compact_and_budget_context(docs, max_tokens=800)


