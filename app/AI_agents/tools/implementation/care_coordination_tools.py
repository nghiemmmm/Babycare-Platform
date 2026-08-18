from app.AI_agents.tools.base_tool import BaseTool
from app.modules.care_coordination.service import CareCoordinationService
from app.modules.care_coordination.schemas import (
    HandoverNoteCreate,
    CareTaskCreate,
    CareTaskCompleteRequest
)


class CareCoordinationTool(BaseTool):
    name = "care_coordination_tool"
    description = (
        "Điều phối lịch trình chăm sóc bé giữa Bố/Mẹ và Người bảo hộ ở nhà. "
        "Hỗ trợ: lấy lịch hôm nay (get_tasks, get_today_summary), "
        "tạo việc cần làm mới (add_task), "
        "đánh dấu hoàn thành cữ chăm sóc (complete_task), "
        "lưu lời dặn buổi sáng cho người ở nhà (save_handover)."
    )

    def _run(self, action: str, baby_id: str, user_id: str, data: dict = None, **kwargs):
        service = CareCoordinationService()
        date_str = kwargs.get("date")

        if action in ("get_today_summary", "summary"):
            summary = service.get_timeline_summary(baby_id, user_id, date_str)
            return summary.model_dump()

        elif action in ("get_tasks", "list_tasks", "tasks"):
            tasks = service.get_today_tasks(baby_id, user_id, date_str)
            return [t.model_dump() for t in tasks]

        elif action in ("add_task", "create_task"):
            if not data:
                return "Error: data is required to create care task"
            data["baby_id"] = baby_id
            task_in = CareTaskCreate(**data)
            return service.create_care_task(task_in, user_id).model_dump()

        elif action in ("complete_task", "mark_done"):
            task_id = kwargs.get("task_id") or (data.get("task_id") if data else None)
            if not task_id:
                return "Error: task_id is required to complete task"
            complete_in = CareTaskCompleteRequest(**(data or {}))
            user_name = kwargs.get("user_name", "AI Assistant")
            return service.complete_task(task_id, complete_in, user_id, user_name).model_dump()

        elif action in ("save_handover", "add_handover"):
            if not data or "content" not in data:
                return "Error: data with content is required to save handover note"
            data["baby_id"] = baby_id
            note_in = HandoverNoteCreate(**data)
            author_name = kwargs.get("author_name", "Phụ huynh")
            return service.save_handover_note(note_in, user_id, author_name).model_dump()

        else:
            return f"Error: unknown action '{action}' for care_coordination_tool"
