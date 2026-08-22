"""
Observability Schemas Module
============================
Pydantic contracts cho Financial & LLMOps Observability:
- TokenBreakdownSchema (Chi tiết token theo từng thành phần)
- FinancialObservabilitySchema (Độ trễ, chi phí USD, tổng token và model)
"""
from typing import Dict, Any
from pydantic import BaseModel, Field


class TokenBreakdownSchema(BaseModel):
    """Chi tiết phân rã token sử dụng theo từng thành phần."""
    system_prompt: int = Field(0, description="Token chỉ dẫn hệ thống")
    profile: int = Field(0, description="Token hồ sơ bé")
    rag_context: int = Field(0, description="Token tài liệu y khoa RAG")
    chat_history: int = Field(0, description="Token lịch sử hội thoại")
    user_query: int = Field(0, description="Token câu hỏi người dùng")
    generation: int = Field(0, description="Token sinh phản hồi")


class FinancialObservabilitySchema(BaseModel):
    """
    Schema báo cáo toàn diện về độ trễ, lượng token và chi phí tài chính (USD).
    """
    latency_ms: int = Field(..., description="Tổng thời gian xử lý toàn bộ pipeline (ms).")
    latency_breakdown: Dict[str, float] = Field(default_factory=dict, description="Phân bổ thời gian cho từng bước.")
    input_tokens: int = Field(0, description="Tổng input tokens tiêu thụ.")
    output_tokens: int = Field(0, description="Tổng completion tokens tiêu thụ.")
    total_tokens: int = Field(0, description="Tổng token sử dụng (input + output).")
    token_breakdown: Dict[str, Any] = Field(default_factory=dict, description="Chi tiết token phân bổ theo thành phần.")
    estimated_cost_usd: float = Field(0.0, description="Chi phí ước tính quy đổi ra USD.")
    model_name: str = Field("gemini-3.5-flash-lite", description="Tên model chính đã xử lý.")

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi sang dict phục vụ log và API response."""
        return self.model_dump()
