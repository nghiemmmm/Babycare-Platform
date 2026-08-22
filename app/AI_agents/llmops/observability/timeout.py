import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TimeoutConfig:
    """
    Quản lý Tập trung Toàn bộ Các Mốc Timeout trong Hệ thống BabyCare AI.
    Khi muốn tăng/giảm thời gian chờ, chỉ cần chỉnh sửa các hằng số tại tệp này.
    """
    # 1. Orchestrator Master Timeouts
    MASTER_EXECUTION_TIMEOUT: float = 90.0      # Timeout tổng bộ máy Multi-Agent
    COMPLEX_TASK_TIMEOUT: float = 120.0          # Timeout cho các tác vụ nặng (Xuất PDF)

    # 2. Tier 3 Fallback Rescue Timeout
    TIER3_RESCUE_TIMEOUT: float = 15.0           # Timeout Web Search cứu hộ tại Tier 3 (Đủ cho Web Search API + LLM Synthesis)

    # 3. Knowledge & RAG Analysis Timeout
    QUERY_ANALYZER_TIMEOUT: float = 5.0          # Timeout Gemini bóc tách SearchPlan


    # 4. Specialist Agent Reasoning Timeout
    REASONER_AGENT_TIMEOUT: float = 15.0         # Timeout LLM suy luận cho từng bước Agent

    # 5. External Tools Timeout
    WEB_SEARCH_TOOL_TIMEOUT: float = 10.0        # Timeout HTTP API Tavily / DuckDuckGo
    TASK_PLANNER_TIMEOUT: float = 15.0           # Timeout API phân loại ý định

    # 6. LLM Provider Connection Timeout
    LLM_PROVIDER_TIMEOUT: float = 30.0           # Timeout HTTP Client cho Gemini / OpenRouter LLM
