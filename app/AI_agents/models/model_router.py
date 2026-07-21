from app.AI_agents.models.llm_factory import LLMFactory
from langchain_core.language_models import BaseChatModel
from app.AI_agents.core import agent_config

class ModelRouter:
    @staticmethod
    def get_model_for_task(task_description: str, token_estimate: int = 0) -> BaseChatModel:
        """
        Dynamically route models based on the task description and estimated token length.
        """
        task_lower = task_description.lower()
        if "reasoning" in task_lower or "report" in task_lower or token_estimate > 10000:
            return LLMFactory.get_model(agent_config.COMPLEX_REASONING_MODEL)
        
        return LLMFactory.get_model(agent_config.DEFAULT_CHAT_MODEL)

