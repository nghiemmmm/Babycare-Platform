import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models import BaseChatModel
from app.core.config import settings
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

class LLMFactory:
    # Cache theo (model_name, temperature) — tránh tạo nhiều HTTP connection pools
    _cache: Dict[Tuple[str, float], ChatGoogleGenerativeAI] = {}

    @classmethod
    def get_model(cls, model_name: str = "gemini-3.5-flash", temperature: float = 0.0) -> ChatGoogleGenerativeAI:
        """
        Factory method trả về LLM instance đã được cache theo (model_name, temperature).
        Lần đầu gọi với một cặp (model, temperature) sẽ tạo mới và cache lại.
        Các lần gọi tiếp theo trả về instance đã có — dùng chung HTTP connection pool.
        """
        cache_key = (model_name, temperature)
        if cache_key not in cls._cache:
            callbacks = []
            if os.getenv("LANGCHAIN_TRACING_V2") == "true":
                try:
                    from langchain_core.tracers import LangChainTracer
                    tracer = LangChainTracer(
                        project_name=os.getenv("LANGCHAIN_PROJECT", "babycare-ai"),
                        api_key=os.getenv("LANGCHAIN_API_KEY")
                    )
                    callbacks.append(tracer)
                except Exception as e:
                    logger.warning(f"[LLMFactory] Could not attach LangChainTracer: {e}")

            target_model = model_name if model_name.startswith("gemini") else "gemini-3.5-flash"
            cls._cache[cache_key] = ChatGoogleGenerativeAI(
                model=target_model,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temperature,
                callbacks=callbacks if callbacks else None
            )
        return cls._cache[cache_key]

    @classmethod
    def clear_cache(cls) -> None:
        """Xóa cache LLM instances. Gọi trong lifespan shutdown để giải phóng HTTP pools."""

