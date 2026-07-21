from app.AI_agents.tools.base_tool import BaseTool
from app.AI_agents.tools.implementation.baby_tools import BabyProfileTool
from app.AI_agents.tools.implementation.growth_tools import GrowthTrackingTool
from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.tools.implementation.nutrition_tools import NutritionTrackingTool
from app.AI_agents.tools.implementation.rag_tools import KnowledgeRetrievalTool
from app.AI_agents.tools.implementation.cry_tools import CryAnalysisTool
from app.AI_agents.tools.implementation.calendar_tool import VaccinationCalendarTool
from app.AI_agents.tools.implementation.email_tool import EmailNotificationTool
from app.AI_agents.tools.implementation.web_search_tool import WebSearchTool
from typing import Dict

class ToolRegistry:
    """
    Registry for all system tools to be accessed dynamically.
    """
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {
            "baby_profile_tool": BabyProfileTool(),
            "growth_tracking_tool": GrowthTrackingTool(),
            "health_records_tool": HealthRecordsTool(),
            "nutrition_tracking_tool": NutritionTrackingTool(),
            "knowledge_retrieval_tool": KnowledgeRetrievalTool(),
            "cry_analysis_tool": CryAnalysisTool(),
            "vaccination_calendar_tool": VaccinationCalendarTool(),
            "email_notification_tool": EmailNotificationTool(),
            "web_search_tool": WebSearchTool(),
        }

    def get_tool(self, name: str) -> BaseTool:
        if name not in self._tools:
            raise ValueError(f"Tool {name} is not registered.")
        return self._tools[name]

    def list_tools(self) -> Dict[str, str]:
        return {name: tool.description for name, tool in self._tools.items()}

tool_registry = ToolRegistry()
