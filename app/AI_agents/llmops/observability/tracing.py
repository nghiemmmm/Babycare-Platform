import os
import logging
from typing import Optional, List, Dict, Any
from langchain_core.callbacks import BaseCallbackHandler

logger = logging.getLogger(__name__)


class LangSmithTracerManager:
    """
    Quản lý tập trung kết nối và Callbacks cho LangSmith Tracing Engine.
    """
    _instance = None
    _tracer = None

    @classmethod
    def get_tracer(cls) -> Optional[BaseCallbackHandler]:
        """
        Khởi tạo và trả về instance LangChainTracer an toàn.
        Bỏ qua nếu LANGCHAIN_TRACING_V2 != 'true'.
        """
        if os.getenv("LANGCHAIN_TRACING_V2") != "true":
            return None

        if cls._tracer is None:
            try:
                from langchain_core.tracers import LangChainTracer
                project_name = os.getenv("LANGCHAIN_PROJECT", "babycare-ai")
                api_key = os.getenv("LANGCHAIN_API_KEY")
                
                # Khởi tạo LangChainTracer chuẩn
                cls._tracer = LangChainTracer(
                    project_name=project_name,
                    client=None  # Sử dụng client mặc định từ biến môi trường
                )
                logger.info(f"[LangSmith] 🚀 Connected to project: '{project_name}'")
            except Exception as e:
                logger.warning(f"[LangSmith] ⚠️ Could not initialize LangChainTracer: {e}")
                return None

        return cls._tracer

    @classmethod
    def get_callbacks(cls) -> List[BaseCallbackHandler]:
        """Trả về danh sách callbacks chuẩn cho LLM Models & Reasoners."""
        tracer = cls.get_tracer()
        return [tracer] if tracer else []

    @classmethod
    def clear(cls):
        """Reset tracer instance cho mục đích testing."""
        cls._tracer = None


def get_tracer_callbacks() -> List[BaseCallbackHandler]:
    """
    Helper ngắn gọn lấy danh sách callbacks cho LLM Factory & AI Reasoner.
    """
    return LangSmithTracerManager.get_callbacks()
