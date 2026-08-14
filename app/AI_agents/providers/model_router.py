import logging
from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel

from app.core.config import settings
from app.AI_agents.core.constant import DEFAULT_CHAT_MODEL, DEFAULT_TEMPERATURE
from app.AI_agents.providers.gemini_provider import GeminiLLMProvider
from app.AI_agents.providers.openrouter_provider import OpenRouterLLMProvider

logger = logging.getLogger(__name__)

class ModelRouter:
    """
    Central Factory & Router quản lý việc tạo đối tượng ChatModel (LLM).
    - Tự động kiểm tra cấu hình settings.LLM_PROVIDER ("openrouter" vs "gemini").
    - Tự động Fallback sang Gemini Provider nếu OpenRouter API Key chưa được thiết lập.
    """

    _gemini_provider = GeminiLLMProvider()
    _openrouter_provider = OpenRouterLLMProvider()

    @classmethod
    def get_model(
        cls,
        model_name: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        callbacks: Optional[List[Any]] = None,
        provider: Optional[str] = None
    ) -> BaseChatModel:
        chosen_provider = (provider or settings.LLM_PROVIDER or "openrouter").lower()

        # Kiểm tra xem OpenRouter API Key có khả dụng không nếu chọn OpenRouter
        if chosen_provider == "openrouter":
            has_key = bool(settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY)
            if not has_key:
                logger.warning(
                    "[ModelRouter] LLM_PROVIDER được cấu hình là 'openrouter' nhưng KHÔNG có OPENROUTER_API_KEY! "
                    "Tự động Auto-Fallback sang GeminiLLMProvider."
                )
                chosen_provider = "gemini"

        if chosen_provider == "openrouter":
            try:
                target_model = model_name or settings.OPENROUTER_MODEL or "google/gemini-3.5-flash-001"
                return cls._openrouter_provider.get_chat_model(
                    model_name=target_model,
                    temperature=temperature,
                    timeout=timeout,
                    max_retries=max_retries,
                    callbacks=callbacks
                )
            except Exception as e:
                logger.error(f"[ModelRouter] Khởi tạo OpenRouterLLMProvider thất bại ({e}). Fallback sang Gemini Provider.")
                return cls._gemini_provider.get_chat_model(
                    model_name=DEFAULT_CHAT_MODEL,
                    temperature=temperature,
                    timeout=timeout,
                    max_retries=max_retries,
                    callbacks=callbacks
                )

        # Mặc định sử dụng Gemini Provider
        target_model = model_name or DEFAULT_CHAT_MODEL
        return cls._gemini_provider.get_chat_model(
            model_name=target_model,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
            callbacks=callbacks
        )
