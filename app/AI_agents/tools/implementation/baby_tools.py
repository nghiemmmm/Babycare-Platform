from app.AI_agents.tools.base_tool import BaseTool
from app.modules.baby.service import BabyService
from app.modules.baby.schemas import BabyCreate, BabyUpdate

class BabyProfileTool(BaseTool):
    name = "baby_profile_tool"
    description = "Retrieve or update baby profiles. Actions: get_baby, get_my_babies, create_baby, update_baby."

    def _run(self, action: str, user_id: str, baby_id: str = None, data: dict = None):
        service = BabyService()
        if action == "get_baby":
            if not baby_id:
                return "Error: baby_id is required for get_baby"
            return service.get_baby_by_id(baby_id, user_id).model_dump()
        elif action == "get_my_babies":
            return [b.model_dump() for b in service.get_my_babies(user_id)]
        elif action == "create_baby":
            if not data:
                return "Error: data dict is required for create_baby"
            baby_in = BabyCreate(**data)
            return service.create_baby(baby_in, user_id).model_dump()
        elif action == "update_baby":
            if not baby_id or not data:
                return "Error: baby_id and data are required for update_baby"
            baby_update = BabyUpdate(**data)
            return service.update_baby(baby_id, baby_update, user_id).model_dump()
        else:
            return f"Error: unknown action: {action}"
