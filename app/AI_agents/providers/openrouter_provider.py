import logging
from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.AI_agents.core.constant import DEFAULT_TEMPERATURE, OPENROUTER_FREE_FALLBACK_MODELS
from app.AI_agents.providers.base_provider import BaseLLMProvider

logger = logging.getLogger(__name__)

import httpx

_shared_async_client: Optional[httpx.AsyncClient] = None

def _get_shared_async_client() -> httpx.AsyncClient:
    global _shared_async_client
    if _shared_async_client is None or _shared_async_client.is_closed:
        _shared_async_client = httpx.AsyncClient(
            limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
            timeout=httpx.Timeout(60.0, connect=5.0)
        )
    return _shared_async_client


class OpenRouterLLMProvider(BaseLLMProvider):
    """
    LLM Provider dành cho OpenRouter API (OpenAI-compatible).
    Hỗ trợ kết nối đa dạng mô hình và tự động chuyển giao Fallback Array:
    Google Gemma -> OpenAI GPT-OSS -> GLM 5.2 -> LFM.
    """

    def get_chat_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = DEFAULT_TEMPERATURE,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        callbacks: Optional[List[Any]] = None
    ) -> BaseChatModel:
        target_model = model_name or settings.OPENROUTER_MODEL or OPENROUTER_FREE_FALLBACK_MODELS[0]
        if "/" not in target_model:
            if "gemini" in target_model:
                target_model = "google/gemini-3.5-flash-001"
            elif "llama" in target_model:
                target_model = "meta-llama/llama-3.3-70b-instruct"
        api_key = settings.OPENROUTER_API_KEY or settings.OPENAI_API_KEY

        if not api_key:
            logger.warning("[OpenRouterLLMProvider] KHÔNG tìm thấy OPENROUTER_API_KEY trong settings!")

        base_url = settings.OPENROUTER_BASE_URL or "https://openrouter.ai/api/v1"

        default_headers = {
            "HTTP-Referer": "https://babycare.ai",
            "X-Title": "BabyCare AI Platform"
        }

        # Danh sách Fallback Cascade tự động của OpenRouter
        models_cascade = [target_model] + [m for m in OPENROUTER_FREE_FALLBACK_MODELS if m != target_model]

        # Pre-warm get_platform trên Windows để tránh asyncio.to_thread(get_platform) bị hang/cancelled
        try:
            import openai._base_client as _obc
            if hasattr(_obc, "get_platform"):
                _obc.get_platform()
        except Exception:
            pass

        logger.info(f"[OpenRouterLLMProvider] Initializing ChatOpenAI via OpenRouter: primary='{target_model}', cascade={models_cascade}")

        return ChatOpenAI(
            model=target_model,
            openai_api_key=api_key,
            openai_api_base=base_url,
            temperature=temperature,
            timeout=timeout or settings.LLM_TIMEOUT_SECONDS,
            max_retries=max_retries or settings.LLM_MAX_RETRIES,
            default_headers=default_headers,
            model_kwargs={
                "extra_body": {
                    "models": models_cascade
                }
            },
            http_async_client=_get_shared_async_client(),
            callbacks=callbacks
        )

