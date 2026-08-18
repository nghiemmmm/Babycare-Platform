import re
import time
import uuid
import logging
from datetime import datetime, date, timezone
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger(__name__)


def extract_user_query(state_or_messages: Any) -> str:
    """
    Trích xuất nội dung câu hỏi/tin nhắn cuối cùng của người dùng một cách an toàn.

    Hỗ trợ đa dạng cấu trúc đầu vào:
    - OverallState dict chứa key 'messages'
    - Danh sách các đối tượng BaseMessage (HumanMessage, AIMessage...)
    - Danh sách các dictionary message [{'role': 'user', 'content': '...'}]
    - Chuỗi văn bản string thuần túy.

    Args:
        state_or_messages (Any): State hoặc danh sách tin nhắn cần trích xuất.

    Returns:
        str: Chuỗi văn bản câu hỏi của người dùng (trả về chuỗi rỗng nếu không tìm thấy).
    """
    if not state_or_messages:
        return ""

    messages = state_or_messages
    if isinstance(state_or_messages, dict):
        messages = state_or_messages.get("messages", [])

    if isinstance(messages, str):
        return messages.strip()

    if not isinstance(messages, list) or len(messages) == 0:
        return str(state_or_messages).strip()

    for msg in reversed(messages):
        # 1. Đối tượng LangChain BaseMessage (HumanMessage)
        if hasattr(msg, "type") and msg.type == "human":
            return getattr(msg, "content", "").strip()
        # 2. Dict message với role 'user'
        if isinstance(msg, dict) and msg.get("role") in ["user", "human"]:
            return msg.get("content", "").strip()
        # 3. Message object thông thường có content
        if hasattr(msg, "content") and getattr(msg, "content", None):
            return str(getattr(msg, "content")).strip()
        # 4. Dict thông thường có key 'content'
        if isinstance(msg, dict) and "content" in msg:
            return str(msg["content"]).strip()

    # Fallback phần tử cuối cùng
    last_item = messages[-1]
    if isinstance(last_item, dict):
        return last_item.get("content", "")
    if hasattr(last_item, "content"):
        return getattr(last_item, "content", "")
    return str(last_item).strip()


def build_tool_step(
    tool_name: str,
    display_name: str,
    result_summary: str = "",
    args: Optional[Dict[str, Any]] = None,
    duration_ms: int = 0,
    status: str = "completed",
    step_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Tạo đối tượng ToolStep chuẩn hóa cho UI hiển thị tiến trình và LLMOps Observability.

    Args:
        tool_name (str): Tên kỹ thuật của công cụ (ví dụ: 'MedicalRetriever', 'HealthRecordsTool').
        display_name (str): Tên hiển thị thân thiện trên giao diện người dùng.
        result_summary (str): Tóm tắt ngắn gọn kết quả thực thi của công cụ.
        args (Optional[Dict[str, Any]]): Tham số đầu vào đã truyền cho công cụ.
        duration_ms (int): Thời gian thực thi tính bằng mili-giây.
        status (str): Trạng thái bước ('completed', 'running', 'failed').
        step_id (Optional[str]): Mã định danh bước (nếu None sẽ tự động sinh ngẫu nhiên).

    Returns:
        Dict[str, Any]: Từ điển ToolStep hợp chuẩn.
    """
    return {
        "id": step_id or f"step_{uuid.uuid4().hex[:6]}",
        "tool_name": tool_name,
        "display_name": display_name,
        "args": args or {},
        "status": status,
        "result_summary": result_summary,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "duration_ms": max(duration_ms, 0)
    }


def calculate_elapsed_ms(start_time: float) -> int:
    """
    Tính toán thời gian đã trôi qua kể từ mốc start_time tính theo mili-giây (ms).

    Args:
        start_time (float): Mốc thời gian bắt đầu (từ time.time() hoặc time.perf_counter()).

    Returns:
        int: Số mili-giây đã trôi qua.
    """
    return int((time.time() - start_time) * 1000)


def calculate_baby_age(birth_date: str) -> dict:
    """
    Tính toán tuổi chính xác của bé từ ngày sinh định dạng ISO (YYYY-MM-DD).

    Args:
        birth_date (str): Chuỗi ngày sinh dạng ISO.

    Returns:
        dict: Chứa các trường 'months' (tổng số tháng), 'days' (tổng số ngày) và 'display' (chuỗi hiển thị tiếng Việt).
    """
    try:
        bd = datetime.fromisoformat(birth_date[:10]).date()
    except Exception:
        return {"months": 0, "days": 0, "display": "Không xác định"}
    
    today = date.today()
    delta = relativedelta(today, bd)
    total_months = delta.years * 12 + delta.months
    display = f"{delta.years} tuổi {delta.months} tháng {delta.days} ngày" if delta.years >= 1 else \
              f"{total_months} tháng {delta.days} ngày" if total_months >= 1 else \
              f"{(today - bd).days} ngày tuổi"
    
    return {"months": total_months, "days": (today - bd).days, "display": display}


def clean_query_text(text: str) -> str:
    """
    Làm sạch câu truy vấn của người dùng: loại bỏ khoảng trắng thừa và dấu câu dư ở cuối câu.

    Args:
        text (str): Chuỗi câu hỏi gốc.

    Returns:
        str: Chuỗi câu hỏi đã được làm sạch.
    """
    if not text:
        return ""
    t = text.strip()
    return re.sub(r"[!.,~?:\-=_]+$", "", t).strip()


def format_agent_response(content: str, next_step: Optional[str] = None) -> dict:
    """
    Đóng gói payload phản hồi cơ bản của Agent.

    Args:
        content (str): Nội dung văn bản câu trả lời.
        next_step (Optional[str]): Bước kế tiếp nếu có.

    Returns:
        dict: Từ điển {'response': content, 'next_step': next_step}.
    """
    return {"response": content, "next_step": next_step}


def sanitize_baby_id(baby_id: Optional[str]) -> Optional[str]:
    """
    Làm sạch mã định danh bé: loại bỏ khoảng trắng và trả về None nếu rỗng.

    Args:
        baby_id (Optional[str]): ID bé đầu vào.

    Returns:
        Optional[str]: ID đã được làm sạch hoặc None.
    """
    if not baby_id:
        return None
    sanitized = baby_id.strip()
    return sanitized if sanitized else None
