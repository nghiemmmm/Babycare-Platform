from app.AI_agents.models.llm_factory import LLMFactory
from langchain_core.language_models import BaseChatModel

class ModelRouter:
    @staticmethod
    def get_model_for_task(task_description: str, token_estimate: int = 0) -> BaseChatModel:
        """
        Dynamically route models based on the task description and estimated token length.
        """
        task_lower = task_description.lower()
        if "reasoning" in task_lower or "report" in task_lower or token_estimate > 10000:
            return LLMFactory.get_model("gemini-1.5-pro")
        
        return LLMFactory.get_model("gemini-2.5-flash")
