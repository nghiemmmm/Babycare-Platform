import re
from typing import Tuple
from app.AI_agents.core.constant import (
    RAG_GREETING_KEYWORDS as GREETING_KEYWORDS,
    RAG_PERSONAL_DB_KEYWORDS as PERSONAL_DB_KEYWORDS,
    RAG_KNOWLEDGE_REQUIRED_KEYWORDS as KNOWLEDGE_REQUIRED_KEYWORDS
)

class RAGTriggerEvaluator:
    """
    Đánh giá xem một query người dùng có thực sự cần kích hoạt RAG retrieval hay không.
    Giúp tiết kiệm Latency, Token Budget và Embedding API calls cho các câu chitchat hoặc tra cứu DB cá nhân.
    """
    GREETING_KEYWORDS = GREETING_KEYWORDS
    PERSONAL_DB_KEYWORDS = PERSONAL_DB_KEYWORDS
    KNOWLEDGE_REQUIRED_KEYWORDS = KNOWLEDGE_REQUIRED_KEYWORDS


    @classmethod
    def should_trigger_rag(cls, query: str) -> Tuple[bool, str]:
        """
        Đánh giá và phân luồng xem một câu hỏi có thực sự cần kích hoạt truy xuất tri thức RAG hay không.

        Quy tắc phân loại:
            1. Chitchat/Greeting Bypass: Các câu chào hỏi, cảm ơn ngắn (< 15 ký tự) -> Không cần RAG.
            2. Knowledge-Required Keywords: Chứa từ khóa y tế, thuốc, ăn dặm, WHO -> Bắt buộc kích hoạt RAG.
            3. Personal DB Profile Bypass: Câu hỏi tra cứu ngày sinh, cân nặng ngắn (< 40 ký tự) -> Bypass RAG.
            4. General Queries: Các câu hỏi dài (> 25 ký tự) -> Kích hoạt RAG tổng quát.

        Args:
            query (str): Nội dung câu hỏi thô từ người dùng.

        Returns:
            Tuple[bool, str]: Tuple gồm (should_trigger, reason_code)
                - should_trigger (bool): True nếu cần kích hoạt RAG, False nếu bỏ qua.
                - reason_code (str): Mã lý do (ví dụ: 'medical_nutrition_guideline', 'chitchat_bypass').

        Raises:
            Không phát sinh ngoại lệ; tự động trả về (False, 'empty_query') nếu câu hỏi rỗng.
        """
        if not query or not query.strip():
            return False, "empty_query"

        query_clean = query.strip().lower()

        # 1. Chitchat / Greeting Bypass (dưới 15 ký tự hoặc chứa từ khóa chào hỏi đơn thuần)
        if len(query_clean) <= 15:
            if any(k in query_clean for k in cls.GREETING_KEYWORDS):
                return False, "chitchat_bypass"

        if query_clean in ["chào bạn", "xin chào", "cảm ơn", "cảm ơn bạn", "tạm biệt", "ok", "dạ"]:
            return False, "chitchat_bypass"

        # 2. ƯU TIÊN HÀNG ĐẦU: Tri thức Y tế / Dinh dưỡng / Phát triển chuẩn WHO -> LUÔN LUÔN KÍCH HOẠT RAG
        if any(k in query_clean for k in cls.KNOWLEDGE_REQUIRED_KEYWORDS):
            return True, "medical_nutrition_guideline"

        # 3. Personal DB Profile Direct Query Fast-Path Bypass (CHỈ ÁP DỤNG cho câu hỏi ngắn dưới 40 ký tự)
        if len(query_clean) <= 40 and any(k in query_clean for k in cls.PERSONAL_DB_KEYWORDS):
            return False, "personal_profile_bypass"

        # 4. Fallback for general queries (> 25 chars)
        if len(query_clean) > 25:
            return True, "general_knowledge_query"

        return False, "default_no_rag"

