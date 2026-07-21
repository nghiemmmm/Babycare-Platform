from langchain_core.callbacks import BaseCallbackHandler
from app.AI_agents.core.logger import get_agent_logger
from typing import Any, Dict, List

logger = get_agent_logger("callback")

class AgentCallbackHandler(BaseCallbackHandler):
    """
    Custom callback handler to capture token usage and LLM execution details.
    """
    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any
    ) -> None:
        logger.info(f"LLM starting with prompts: {prompts}")

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        logger.info(f"LLM execution completed successfully.")

    def on_llm_error(self, error: BaseException, **kwargs: Any) -> None:
        logger.warning(f"LLM encountered error: {str(error)}")
