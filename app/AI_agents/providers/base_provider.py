from abc import ABC, abstractmethod
from typing import Optional, List, Any
from langchain_core.language_models.chat_models import BaseChatModel

class BaseLLMProvider(ABC):
    """
    Abstract Base Class cho tất cả các LLM Provider (OpenRouter, Gemini, OpenAI).
    """

    @abstractmethod
    def get_chat_model(
        self,
        model_name: Optional[str] = None,
        temperature: float = 0.0,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        callbacks: Optional[List[Any]] = None
    ) -> BaseChatModel:
        """
        Trả về đối tượng BaseChatModel (LangChain) sẵn sàng tương tác.
        """
        pass
