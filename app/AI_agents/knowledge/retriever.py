from typing import Optional
from langsmith import traceable
from app.AI_agents.knowledge.rag_pipeline import get_rag_pipeline, compact_and_budget_context
from app.AI_agents.knowledge.query_analyzer import QueryAnalyzer, SearchPlan

from app.AI_agents.llmops.caching.rag_cache import RAGCacheManager

class MedicalRetriever:
    def __init__(self):
        # Dùng singleton RAGPipeline — không tạo FAISS instance mới
        self.pipeline = get_rag_pipeline()
        self.analyzer = QueryAnalyzer()

    @traceable(name="MedicalRetriever.retrieve_context_with_plan")
    async def retrieve_context_with_plan(
        self,
        query: str,
        k: int = 3,
        domain: Optional[str] = None,
        max_tokens: int = 800
    ) -> str:
        """
        Truy xuất tài liệu y khoa nâng cao qua quy trình Hybrid Search có định hướng (Planned Hybrid Retrieval).

        Quy trình xử lý:
            1. Cache Verification: Kiểm tra RAGCacheManager để trả về tức thì nếu đã cache (< 5ms).
            2. Query Understanding: Gọi QueryAnalyzer để lập SearchPlan (keywords + dense_query + filters).
            3. Planned Hybrid Retrieval: Kết hợp FAISS Dense Vector + BM25 Sparse Search qua luồng bất đồng bộ.
            4. Context Compaction & Budgeting: Nén và cắt tỉa văn bản theo giới hạn token (max_tokens).
            5. Cache Storage: Lưu kết quả vào RAG Cache phục vụ các lượt truy vấn tương tự tiếp theo.

        Args:
            query (str): Câu hỏi tự nhiên của người dùng.
            k (int): Số lượng tài liệu liên quan tối đa cần trích xuất (mặc định: 3).
            domain (Optional[str]): Domain chuyên biệt gợi ý lọc dữ liệu ('health', 'nutrition').
            max_tokens (int): Ngân sách token tối đa cho đoạn ngữ cảnh RAG (mặc định: 800 tokens).

        Returns:
            str: Chuỗi văn bản ngữ cảnh y khoa đã được định dạng và nén gọn gàng. Trả về chuỗi rỗng nếu không tìm thấy tài liệu.

        Raises:
            Không phát sinh ngoại lệ; tự động fallback sang tìm kiếm cơ bản hoặc trả về chuỗi rỗng khi gặp sự cố.
        """
        cache_key = RAGCacheManager.generate_key(query, k, domain, max_tokens)
        cached = RAGCacheManager.get(cache_key)
        if cached is not None:
            return cached

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
        RAGCacheManager.set(cache_key, compacted)
        return compacted

    @traceable(name="MedicalRetriever.retrieve_context")
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


