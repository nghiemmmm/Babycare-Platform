"""
Context Schemas Module
======================
Pydantic contracts cho việc gom và chia sẻ ngữ cảnh giữa các Tầng Agent:
- Tier1PreparedContext (Dữ liệu gom không tốn token từ Tier 1 ChatAgent)
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class Tier1PreparedContext(BaseModel):
    """
    Schema đóng gói toàn bộ ngữ cảnh đã gom tại Tier 1 (Profile + RAG WHO)
    sẵn sàng phục vụ cho việc tự giải quyết hoặc tái sử dụng ở Tier 2 (Context Reuse).
    """
    baby_name: str = Field("Bé", description="Tên hiển thị của bé.")
    baby_gender: str = Field("chưa rõ", description="Giới tính của bé (nam/nữ/chưa rõ).")
    baby_age: str = Field("chưa rõ", description="Tuổi / tháng tuổi tính từ ngày sinh.")
    growth_info: str = Field("chưa có dữ liệu", description="Chuỗi thông tin thể chất gần nhất.")
    rag_context: str = Field("", description="Văn bản tài liệu y khoa RAG đã thu thập và nén gọn.")
    tool_steps: List[Dict[str, Any]] = Field(default_factory=list, description="Danh sách các bước tool đã thực thi.")
    context_bundle: Optional[Any] = Field(None, description="ContextBundle nội bộ lưu trữ dữ liệu token.")

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi sang dict tương thích với LangGraph node return."""
        return self.model_dump()
