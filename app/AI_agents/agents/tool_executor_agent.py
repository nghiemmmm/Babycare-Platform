from app.AI_agents.agents.base_agent import BaseAgent
from app.AI_agents.tools.implementation.nutrition_tools import NutritionTrackingTool
from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.tools.implementation.growth_tools import GrowthTrackingTool
from app.AI_agents.tools.implementation.baby_tools import BabyProfileTool

class ToolExecutorAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="ToolExecutorAgent")
        self.nutrition_tool = NutritionTrackingTool()
        self.health_tool = HealthRecordsTool()
        self.growth_tool = GrowthTrackingTool()
        self.baby_tool = BabyProfileTool()

    def execute(self, tool_name: str, action: str, **kwargs):
        if tool_name == "nutrition":
            return self.nutrition_tool._run(action=action, **kwargs)
        elif tool_name == "health":
            return self.health_tool._run(action=action, **kwargs)
        elif tool_name == "growth":
            return self.growth_tool._run(action=action, **kwargs)
        elif tool_name == "baby":
            return self.baby_tool._run(action=action, **kwargs)
        else:
            raise ValueError(f"Unknown tool_name: {tool_name}")
