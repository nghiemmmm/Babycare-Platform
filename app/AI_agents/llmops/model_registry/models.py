import logging
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List

logger = logging.getLogger(__name__)


@dataclass
class LLMModelInfo:
    """
    Schema thông số kỹ thuật của mô hình ngôn ngữ lớn (LLM Specification).
    """
    model_name: str
    provider: str
    context_window: int
    max_output_tokens: int
    supports_tools: bool = True
    supports_vision: bool = False
    description: str = ""


class ModelRegistry:
    """
    Registry quản lý danh mục và thông số kỹ thuật các mô hình LLM trong hệ thống.
    """
    _registry: Dict[str, LLMModelInfo] = {}

    @classmethod
    def register(cls, info: LLMModelInfo):
        """Đăng ký mô hình mới vào Registry."""
        cls._registry[info.model_name] = info

    @classmethod
    def get_info(cls, model_name: str) -> Optional[LLMModelInfo]:
        """Truy xuất thông tin mô hình theo tên."""
        return cls._registry.get(model_name)

    @classmethod
    def list_models(cls) -> List[LLMModelInfo]:
        """Danh sách tất cả các mô hình đã đăng ký."""
        return list(cls._registry.values())

    @classmethod
    def clear(cls):
        """Reset registry cho mục đích testing."""
        cls._registry.clear()


# Mặc định đăng ký các mô hình Gemini chủ lực của hệ thống
ModelRegistry.register(LLMModelInfo(
    model_name="gemini-3.5-flash-lite",
    provider="google",
    context_window=1000000,
    max_output_tokens=8192,
    supports_tools=True,
    description="Mô hình Fast-Path siêu tốc cho các câu trả lời ngắn và câu chào"
))

ModelRegistry.register(LLMModelInfo(
    model_name="gemini-2.0-flash",
    provider="google",
    context_window=1000000,
    max_output_tokens=8192,
    supports_tools=True,
    description="Mô hình Chat tiêu chuẩn cho các Subgraph Agents"
))

ModelRegistry.register(LLMModelInfo(
    model_name="gemini-1.5-pro",
    provider="google",
    context_window=2000000,
    max_output_tokens=8192,
    supports_tools=True,
    description="Mô hình Lập luận chuyên sâu cho Tier 2 Specialist Delegation"
))
