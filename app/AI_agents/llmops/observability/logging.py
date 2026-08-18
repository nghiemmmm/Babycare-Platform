import uuid
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ToolStepLogger:
    """
    Helper chuẩn hóa việc tạo và ghi nhận bước thực thi ToolStep cho các Agent.
    """
    @staticmethod
    def create_step(
        tool_name: str,
        display_name: str,
        args: Optional[Dict[str, Any]] = None,
        result_summary: str = "",
        duration_ms: int = 0,
        status: str = "completed"
    ) -> Dict[str, Any]:
        """Tạo dictionary đại diện cho 1 bước thực thi Tool/Step."""
        return {
            "id": f"step_{uuid.uuid4().hex[:6]}",
            "tool_name": tool_name,
            "display_name": display_name,
            "args": args or {},
            "status": status,
            "result_summary": result_summary,
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": duration_ms
        }

    @staticmethod
    def append_step(state: Dict[str, Any], step: Dict[str, Any]):
        """Thêm bước thực thi vào danh sách tool_steps trong State."""
        if "tool_steps" not in state or state["tool_steps"] is None:
            state["tool_steps"] = []
        state["tool_steps"].append(step)


class AgentExecutionLogger:
    """
    Quản lý tập trung việc ghi log vết thực thi Console và Stream Events cho Agent.
    """
    @staticmethod
    def log_start(run_id: str, trace_id: str, agent_name: str, query: str):
        logger.info(f"📥 [{agent_name}] [Run: {run_id}] [Trace: {trace_id}] Nhận yêu cầu: '{query[:60]}'")

    @staticmethod
    def log_step(run_id: str, trace_id: str, step: Dict[str, Any]):
        display_name = step.get("display_name", step.get("tool_name", "ToolStep"))
        duration = step.get("duration_ms", 0)
        logger.info(f"⚙️ [Run: {run_id}] [Trace: {trace_id}] Thực thi: '{display_name}' ({duration}ms)")

    @staticmethod
    def log_complete(run_id: str, trace_id: str, duration_ms: int):
        logger.info(f"✅ [Run: {run_id}] [Trace: {trace_id}] Hoàn thành xử lý trong {duration_ms}ms")

    @staticmethod
    def log_error(run_id: str, trace_id: str, error: Exception):
        logger.error(f"❌ [Run: {run_id}] [Trace: {trace_id}] Lỗi xử lý: {error}")
