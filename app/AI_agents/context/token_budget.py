import math
from typing import List, Dict, Any, Optional
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, AIMessage
from app.AI_agents.context.context_types import ContextItem, ContextSource

MODEL_PRICING: dict[str, dict[str, float]] = {
    "gemini-3.5-flash-lite": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
    "gemini-1.5-flash-latest": {"input": 0.075, "output": 0.30},
    "gemini-1.5-pro": {"input": 1.25, "output": 5.00},
    "default": {"input": 0.10, "output": 0.40}
}


class TokenBudget:
    """
    Token Estimator & Global Budget Allocator cho Context Builder.
    Quy tắc ước tính: ~1.3 tokens per word cho hỗn hợp Tiếng Việt / Tiếng Anh.
    """
    DEFAULT_MAX_INPUT_TOKENS = 4000
    SYSTEM_INSTRUCTION_MAX = 500
    CONVERSATION_HISTORY_MAX = 1000
    RAG_MAX_TOKENS = 800

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        words = text.strip().split()
        return math.ceil(len(words) * 1.3)

    @staticmethod
    def estimate_message_tokens(msg: AnyMessage) -> int:
        content = getattr(msg, "content", "")
        if isinstance(content, str):
            return TokenBudget.estimate_tokens(content) + 4  # message metadata overhead
        return 10

    @staticmethod
    def allocate_items(
        items: List[ContextItem],
        max_budget: int = DEFAULT_MAX_INPUT_TOKENS
    ) -> List[ContextItem]:
        """
        Phân bổ items theo thứ tự ưu tiên (Priority từ cao xuống thấp).
        Chỉ giữ lại các items nằm trong tổng Token Budget.
        """
        sorted_items = sorted(items, key=lambda x: (x.priority, x.relevance_score), reverse=True)
        allocated: List[ContextItem] = []
        accumulated_tokens = 0

        for item in sorted_items:
            if item.token_count == 0:
                item.token_count = TokenBudget.estimate_tokens(item.content)

            if item.source == ContextSource.RAG_DOCS:
                # Cap RAG docs at 800 tokens max
                if item.token_count > TokenBudget.RAG_MAX_TOKENS:
                    # Truncate content to budget
                    words = item.content.split()
                    max_words = int(TokenBudget.RAG_MAX_TOKENS / 1.3)
                    item.content = " ".join(words[:max_words]) + "..."
                    item.token_count = TokenBudget.RAG_MAX_TOKENS

            if accumulated_tokens + item.token_count <= max_budget:
                allocated.append(item)
                accumulated_tokens += item.token_count

        return allocated

    @staticmethod
    def calculate_cost_usd(model_name: str, input_tokens: int, output_tokens: int) -> float:
        """
        Tính toán chi phí USD dựa trên Model Pricing per 1M tokens.
        """
        rates = MODEL_PRICING.get(model_name, MODEL_PRICING.get("default", {"input": 0.10, "output": 0.40}))
        cost_input = (input_tokens / 1_000_000.0) * rates["input"]
        cost_output = (output_tokens / 1_000_000.0) * rates["output"]
        return round(cost_input + cost_output, 7)
