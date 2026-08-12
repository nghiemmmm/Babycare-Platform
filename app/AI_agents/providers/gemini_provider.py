import logging
from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.AI_agents.core.constant import DEFAULT_CHAT_MODEL, DEFAULT_TEMPERATURE
from app.AI_agents.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

class GeminiLLMProvider(BaseLLMProvider):
    """
    LLM Provider dành cho Google Gemini API (gốc).
    """

    def get_chat_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        callbacks: Optional[List[Any]] = None
    ) -> BaseChatModel:
        target_model = model_name or DEFAULT_CHAT_MODEL
        # Nếu model_name chứa prefix provider dạng 'google/gemini-3.5-flash-001', tách lấy phần tên model
        if "/" in target_model:
            target_model = target_model.split("/")[-1]

        # Bảo vệ: Nếu model_name thuộc dòng Gemini/Gemma -> giữ nguyên, nếu là provider khác -> Fallback sang gemini-3.5-flash
        valid_gemini_keywords = ["gemini", "gemma"]
        if not any(k in target_model.lower() for k in valid_gemini_keywords):
            logger.warning(f"[GeminiLLMProvider] Model '{target_model}' không thuộc Google AI Studio Native Models! Auto-Fallback sang 'gemini-3.5-flash'.")
            target_model = "gemini-3.5-flash"

        api_key = settings.GEMINI_API_KEY
        if not api_key:
            logger.warning("[GeminiLLMProvider] GEMINI_API_KEY không được tìm thấy trong settings!")

        return ChatGoogleGenerativeAI(
            model=target_model,
            google_api_key=api_key,
            temperature=temperature,
            timeout=timeout or settings.LLM_TIMEOUT_SECONDS,
            max_retries=max_retries or settings.LLM_MAX_RETRIES,
            callbacks=callbacks
        )
