from typing import List, Dict, Any, Optional

import logging
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import settings

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

    async def analyze(self, user_query: str, domain_hint: Optional[str] = None) -> SearchPlan:
        """
        Bóc tách câu hỏi người dùng thành SearchPlan.
        Nếu gặp lỗi hoặc không gọi được LLM, tự động fallback về SearchPlan cơ bản.
        """
        if not user_query or not user_query.strip():
            return SearchPlan(
                intent="GENERAL",
                keywords=[],
                dense_query=user_query,
                filters={}
            )

        # ── FAST-PATH: Skip LLM call for short, simple queries (save 300–800ms) ──
        COMPLEX_KEYWORDS = [
            "lịch sử", "14 ngày", "7 ngày", "phân tích", "biểu đồ",
            "nhật ký", "so sánh", "xu hướng", "hapacol", "overdose",
            "co giật", "khó thở", "tím tái", "dựa trên"
        ]
        is_simple = len(user_query.strip()) <= 80 and not any(kw in user_query.lower() for kw in COMPLEX_KEYWORDS)
        if is_simple:
            words = [w.strip("?,./!").lower() for w in user_query.split() if len(w) > 2]
            filters: Dict[str, Any] = {}
            # Lightweight domain detection (no LLM)
            q_lower = user_query.lower()
            if any(k in q_lower for k in ["ăn", "bú", "sữa", "kcal", "dinh dưỡng", "calo"]):
                filters["category"] = "nutrition"
            elif any(k in q_lower for k in ["sốt", "ốm", "bệnh", "thuốc", "tiêm"]):
                filters["category"] = "health"
            return SearchPlan(
                intent="GENERAL",
                keywords=words[:5],
                dense_query=user_query,
                filters=filters
            )

        if self.llm is not None:
            try:
                import asyncio
                prompt = (
                    f"Bạn là chuyên gia phân tích truy vấn y tế nhi khoa.\n"
                    f"Hãy bóc tách câu hỏi tự nhiên của phụ huynh sau đây thành một SearchPlan có cấu trúc:\n"
                    f"Câu hỏi: \"{user_query}\"\n"
                    f"Gợi ý Domain: \"{domain_hint or 'Không có'}\"\n\n"
                    f"Lưu ý:\n"
                    f"- keywords: Lấy 2-5 từ khóa quan trọng nhất cho BM25 search (viết thường).\n"
                    f"- dense_query: Viết lại câu hỏi đầy đủ ngữ nghĩa y khoa chuẩn xác.\n"
                    f"- filters: Thêm 'category': 'health' hoặc 'nutrition' nếu xác định rõ."
                )
                plan: SearchPlan = await asyncio.wait_for(self.llm.ainvoke(prompt), timeout=2.0)
                if not plan.dense_query:
                    plan.dense_query = user_query
                return plan
            except Exception as e:
                logger.warning(f"[QueryAnalyzer] Fallback do lỗi phân tích LLM / Timeout: {e}")

        # Basic Fallback
        words = [w.strip("?,.").lower() for w in user_query.split() if len(w) > 2]
        filters = {}
        if domain_hint:
            filters["domain"] = domain_hint

        return SearchPlan(
            intent="GENERAL",
            keywords=words[:5],
            dense_query=user_query,
            filters=filters
        )
