from typing import List, Dict, Any, Optional

import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings
from app.AI_agents.llmops.observability.timeout import TimeoutConfig

logger = logging.getLogger(__name__)

class SearchPlan(BaseModel):
    """
    Cấu trúc kế hoạch tìm kiếm đã chuẩn hóa trích xuất từ câu hỏi tự nhiên.
    """
    intent: str = Field(
        default="GENERAL",
        description="Nhóm ý định: NUTRITION, HEALTH_MEDICATION, GROWTH, hoặc GENERAL"
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Từ khóa cốt lõi dành riêng cho BM25 Sparse Search (VD: ['hapacol', 'sốt', '150mg'])"
    )
    dense_query: str = Field(
        default="",
        description="Câu query chuẩn hóa ngữ nghĩa dành riêng cho FAISS Dense Search"
    )
    filters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Bộ lọc metadata tùy chọn (VD: {'category': 'health'})"
    )


from langsmith import traceable

class QueryAnalyzer:
    """
    Module phân tích và chuyển đổi câu hỏi mơ hồ (Ambiguous Request) thành SearchPlan có cấu trúc.
    Sử dụng model Gemini Flash lightweight 100% miễn phí.
    """
    def __init__(self):
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            try:
                from app.AI_agents.core.constant import QUERY_ANALYZER_MODEL, QUERY_ANALYZER_PROVIDER
                from app.AI_agents.providers.model_router import ModelRouter

                raw_llm = ModelRouter.get_model(model_name=QUERY_ANALYZER_MODEL, provider=QUERY_ANALYZER_PROVIDER, temperature=0.0)
                self._llm = raw_llm.with_structured_output(SearchPlan)
            except Exception as e:
                logger.warning(f"[QueryAnalyzer] Không thể khởi tạo Structured Output LLM: {e}")
                self._llm = None
            return self._llm
        return self._llm

    @traceable(name="QueryAnalyzer.analyze")
    async def analyze(self, user_query: str, domain_hint: Optional[str] = None) -> SearchPlan:
        """
        Bóc tách câu hỏi tự nhiên của người dùng thành Kế hoạch Tìm kiếm có cấu trúc (SearchPlan) cho Hybrid RAG.

        Chiến lược phân luồng (Two-mode Routing):
            1. Fast-Path Pure Python: Với câu hỏi ngắn, trực tiếp (< 15 từ, < 150 ký tự), tự động lọc
               stop words và gán metadata filters bằng code trong < 0.1ms (0 Token LLM).
            2. LLM Deep Analysis: Với câu hỏi mơ hồ, phức tạp, đa triệu chứng, kích hoạt Gemini Flash Lite
               để cấu trúc hóa ngữ nghĩa y khoa chuẩn xác.

        Args:
            user_query (str): Câu hỏi tự nhiên của người dùng.
            domain_hint (Optional[str]): Gợi ý domain chuyên môn nếu có (ví dụ: 'health', 'nutrition').

        Returns:
            SearchPlan: Đối tượng kế hoạch tìm kiếm chứa:
                - intent: Nhóm ý định ('HEALTH_MEDICATION', 'NUTRITION', 'GROWTH', 'GENERAL').
                - keywords: Danh sách 2-5 từ khóa chọn lọc cho BM25 Sparse Search.
                - dense_query: Câu truy vấn ngữ nghĩa chuẩn hóa cho FAISS Dense Search.
                - filters: Bộ lọc metadata chuyên môn (ví dụ: {'category': 'health'}).

        Raises:
            Không phát sinh ngoại lệ; tự động fallback về SearchPlan cơ bản nếu gặp lỗi hoặc timeout khi gọi LLM.
        """
        if not user_query or not user_query.strip():
            return SearchPlan(
                intent="GENERAL",
                keywords=[],
                dense_query=user_query,
                filters={}
            )

        q_lower = user_query.lower()

        # ── 1. ĐIỀU KIỆN KÍCH HOẠT LLM CHO CÂU HỎI MƠ HỒ / PHỨC TẠP / NHIỀU TRIỆU CHỨNG ──
        AMBIGUOUS_AND_COMPLEX_SIGNALS = [
            "tại sao", "vì sao", "lý do gì", "có sao không", "có bình thường không",
            "dạo này", "mấy hôm nay", "mấy ngày qua", "vừa", "kết hợp", "kèm theo",
            "nhưng", "nếu", "thì có được", "triệu chứng", "đi ngoài", "phân sống",
            "phân lỏng", "nhầy", "nôn trớ", "co giật", "khó thở", "tím tái",
            "lười ăn", "không chịu bú", "quấy khóc đêm", "so với", "chuẩn who như thế nào"
        ]
        
        is_ambiguous_or_complex = (
            any(sig in q_lower for sig in AMBIGUOUS_AND_COMPLEX_SIGNALS)
            or len(user_query.strip()) > 150
            or ("?" in user_query and len(user_query.split()) > 15)
        )

        # Nếu câu hỏi khó hiểu / mơ hồ / nhiều triệu chứng -> Gọi LLM phân tích sâu
        if is_ambiguous_or_complex and self.llm is not None:
            try:
                import asyncio
                prompt = (
                    f"Bạn là chuyên gia phân tích truy vấn y tế nhi khoa.\n"
                    f"Hãy bóc tách câu hỏi tự nhiên sau thành SearchPlan chuẩn y khoa:\n"
                    f"Câu hỏi: \"{user_query}\"\n"
                    f"Gợi ý Domain: \"{domain_hint or 'Không có'}\"\n\n"
                    f"Yêu cầu:\n"
                    f"- keywords: 2-5 từ khóa quan trọng nhất cho BM25 search (viết thường).\n"
                    f"- dense_query: Viết lại câu hỏi đầy đủ ngữ nghĩa y khoa chuẩn xác.\n"
                    f"- filters: Thêm 'category': 'health' hoặc 'nutrition' nếu xác định rõ."
                )
                plan: SearchPlan = await asyncio.wait_for(self.llm.ainvoke(prompt), timeout=10.0)
                if not plan.dense_query:
                    plan.dense_query = user_query
                return plan
            except Exception as e:
                logger.warning(f"[QueryAnalyzer] Fallback từ LLM sang Fast-Path: {e}")

        # ── 2. FAST-PATH CHO CÂU HỎI ĐƠN GIẢN / TRỰC TIẾP (< 0.1ms, 0 Token) ──
        STOP_WORDS = {
            "cần", "cho", "với", "mỗi", "ngày", "theo", "của", "được", "không",
            "thì", "làm", "sao", "bao", "nhiêu", "như", "thế", "nào", "bé", "mẹ"
        }
        words = [
            w.strip("?,./!").lower()
            for w in user_query.split()
            if len(w) > 1 and w.strip("?,./!").lower() not in STOP_WORDS
        ]
        
        filters: Dict[str, Any] = {}
        if any(k in q_lower for k in ["ăn", "bú", "sữa", "kcal", "dinh dưỡng", "calo", "cháo", "bột", "dị ứng"]):
            filters["category"] = "nutrition"
        elif any(k in q_lower for k in ["sốt", "ốm", "bệnh", "thuốc", "tiêm", "vitamin", "d3", "canxi", "hapacol", "paracetamol", "vắc xin"]):
            filters["category"] = "health"

        return SearchPlan(
            intent="HEALTH_MEDICATION" if "health" in filters.values() else ("NUTRITION" if "nutrition" in filters.values() else "GENERAL"),
            keywords=words[:6],
            dense_query=user_query,
            filters=filters
        )

