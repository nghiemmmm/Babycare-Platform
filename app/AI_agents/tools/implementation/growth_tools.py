from app.AI_agents.tools.base_tool import BaseTool
from app.modules.growth_tracking.service import GrowthTrackingService
from app.modules.growth_tracking.schemas import GrowthLogCreate

class GrowthTrackingTool(BaseTool):
    name = "growth_tracking_tool"
    description = "Log physical growth metrics (height, weight, head_circumference) and analyze WHO percentiles. Requires baby_id, user_id, action (add/history)."

    def _run(self, action: str, baby_id: str, user_id: str, data: dict = None, **kwargs):
        service = GrowthTrackingService()
        if action == "add":
            if not data:
                return "Error: data is required to add growth log"
            log_in = GrowthLogCreate(**data)
            return service.add_growth_log(baby_id, log_in, user_id).model_dump()
        elif action in ("history", "get_history", "list"):
            limit = kwargs.get("limit")
            logs = [g.model_dump() for g in service.get_growth_history(baby_id, user_id)]
            if limit and isinstance(limit, int):
                return logs[:limit]
            return logs
        else:
            return f"Error: unknown action: {action}"

