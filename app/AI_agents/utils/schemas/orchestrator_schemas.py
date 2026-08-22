"""
Orchestrator Schemas Module
===========================
Pydantic contracts cho đầu ra của Master Orchestrator Pipeline:
- AgentExecutionResult (Kết quả thực thi chuẩn hóa trả về từ run_agent)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from app.AI_agents.utils.schemas.observability_schemas import FinancialObservabilitySchema


class AgentExecutionResult(BaseModel):
    """
    Schema kết quả trả về chuẩn hóa của AgentOrchestrator.run_agent.
    """
    messages: List[Any] = Field(default_factory=list, description="Danh sách các tin nhắn hội thoại bao gồm câu trả lời của AI.")
    tool_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách chi tiết các công cụ đã được kích hoạt.")
    rag_context: Optional[str] = Field(None, description="Ngữ cảnh tri thức y tế đã sử dụng nếu có.")
    extracted_data: Optional[Dict[str, Any]] = Field(None, description="Dữ liệu trích xuất nhật ký chăm sóc bé nếu có.")
    next_step: Optional[str] = Field(None, description="Bước kế tiếp trong quy trình.")
    financial_observability: Optional[FinancialObservabilitySchema] = Field(None, description="Chỉ số phân tích tài chính, độ trễ và token.")
    context_bundle: Optional[Any] = Field(None, description="Gói ngữ cảnh tính toán token nội bộ.")

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi sang dict tương thích với các router API của FastAPI."""
        return self.model_dump(exclude_none=True)
