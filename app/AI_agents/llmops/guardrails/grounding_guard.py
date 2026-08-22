import logging
from typing import Optional

logger = logging.getLogger(__name__)

GROUNDING_DISCLAIMER = (
    "\n\n*(Lưu ý: Chưa tìm thấy tài liệu y tế trực tiếp trong cơ sở dữ liệu cho câu hỏi này. "
    "Thông tin dựa trên nguyên tắc nhi khoa chung, xin hãy tham khảo ý kiến bác sĩ chuyên khoa.)*"
)


class GroundingGuard:
    """
    Module kiểm tra và gắn disclaimer chống ảo giác (Anti-hallucination Grounding Guard) trong LLMOps Guardrails.
    """
    @staticmethod
    def apply_grounding_guard(response_text: str, rag_context: Optional[str] = None) -> str:
        """
        Đảm bảo câu trả lời được hỗ trợ bởi bằng chứng y tế (evidence).
        Nếu thiếu evidence hoặc context thông báo không tìm thấy tài liệu ➔ Gắn disclaimer nhi khoa.
        """
        if not response_text:
            return response_text

        # Kiểm tra nếu RAG context trống hoặc không chứa tài liệu y tế thực sự
        is_unsupported = (
            not rag_context or 
            "Không tìm thấy tài liệu y tế phù hợp" in rag_context or
            "Nguồn tài liệu:" not in rag_context and "--- Tài liệu" not in rag_context
        )

        if is_unsupported and GROUNDING_DISCLAIMER not in response_text:
            logger.info("[GroundingGuard] ⚠️ Gắn disclaimer chống ảo giác y tế do thiếu evidence RAG.")
            return f"{response_text.strip()}{GROUNDING_DISCLAIMER}"

        return response_text
