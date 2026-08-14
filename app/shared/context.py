"""
Distributed Tracing & Context Propagation Module

Sử dụng contextvars của Python để lưu giữ trace_id xuyên suốt toàn bộ vòng đời
từ HTTP Middleware ➔ Orchestrator ➔ RAG ➔ LLM Reasoner ➔ SSE Response.
"""
import uuid
import contextvars
from typing import Dict

# ContextVar lưu giữ trace_id cho từng request/thread
request_trace_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_trace_id", default="")

# ContextVar lưu giữ chi phí tích lũy (USD) cho từng request/trace_id
request_accumulated_cost: contextvars.ContextVar[float] = contextvars.ContextVar("request_accumulated_cost", default=0.0)


def get_current_trace_id() -> str:
    """Trả về trace_id hiện tại. Nếu chưa có, tự động sinh mới dạng trace_xxxx."""
    tid = request_trace_id.get()
    if not tid:
        tid = f"trace_{uuid.uuid4().hex[:12]}"
        request_trace_id.set(tid)
    return tid


def add_task_cost(cost_usd: float) -> float:
    """Cộng dồn chi phí USD của một cú gọi LLM vào tổng chi phí của trace_id hiện tại."""
    current = request_accumulated_cost.get()
    updated = round(current + cost_usd, 7)
    request_accumulated_cost.set(updated)
    return updated


def get_accumulated_cost() -> float:
    """Trả về tổng chi phí USD của trace_id hiện tại."""
    return request_accumulated_cost.get()
