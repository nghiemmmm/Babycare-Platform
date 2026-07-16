from app.AI_agents.tools.base_tool import BaseTool
from app.modules.nutrition.service import SolidFoodService
from app.modules.nutrition.schemas import SolidFoodLogCreate

class NutritionTrackingTool(BaseTool):
    name = "nutrition_tracking_tool"
    description = "Log solid food meals, feed amounts, and baby physical reactions. Actions: add, history."

    def _run(self, action: str, baby_id: str, user_id: str, data: dict = None):
        service = SolidFoodService()
        if action == "add":
            if not data:
                return "Error: data is required to add nutrition log"
            log_in = SolidFoodLogCreate(**data)
            return service.add_solid_food_log(baby_id, log_in, user_id).model_dump()
        elif action == "history":
            return [n.model_dump() for n in service.get_solid_food_history(baby_id, user_id)]
        else:
            return f"Error: unknown action: {action}"
