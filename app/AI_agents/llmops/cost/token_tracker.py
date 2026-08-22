from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


@dataclass
class TokenBreakdown:
    """
    Schema phân rã số lượng Token tiêu thụ theo từng nguồn thành phần.
    """
    system_instruction: int = 0
    long_term_facts: int = 0
    rag_docs: int = 0
    conversation_summary: int = 0
    recent_messages: int = 0
    completion_output: int = 0

    @property
    def total_input_tokens(self) -> int:
        return (
            self.system_instruction
            + self.long_term_facts
            + self.rag_docs
            + self.conversation_summary
            + self.recent_messages
        )

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.completion_output

    def to_dict(self) -> Dict[str, int]:
        return {
            "system_instruction": self.system_instruction,
            "long_term_facts": self.long_term_facts,
            "rag_docs": self.rag_docs,
            "conversation_summary": self.conversation_summary,
            "recent_messages": self.recent_messages,
            "completion_output": self.completion_output,
            "total_input_tokens": self.total_input_tokens,
            "total_tokens": self.total_tokens
        }


class TokenMetricsTracker:
    """
    Bộ bóc tách và phân phân rã chỉ số Token từ ContextBundle và kết quả sinh LLM.
    """
    @staticmethod
    def from_context_bundle(context_bundle: Any, completion_text: str = "") -> TokenBreakdown:
        from app.AI_agents.context.token_budget import TokenBudget
        
        breakdown = TokenBreakdown()
        
        if not context_bundle:
            if completion_text:
                breakdown.completion_output = TokenBudget.estimate_tokens(str(completion_text))
            return breakdown

        token_map = {}
        if hasattr(context_bundle, "token_breakdown"):
            token_map = getattr(context_bundle, "token_breakdown", {})
        elif isinstance(context_bundle, dict):
            token_map = context_bundle.get("token_breakdown", {})

        breakdown.system_instruction = token_map.get("SYSTEM_INSTRUCTION", 0)
        breakdown.long_term_facts = token_map.get("LONG_TERM_FACTS", 0)
        breakdown.rag_docs = token_map.get("RAG_DOCS", 0)
        breakdown.conversation_summary = token_map.get("CONVERSATION_SUMMARY", 0)
        breakdown.recent_messages = token_map.get("RECENT_MESSAGES", 0)

        if completion_text:
            breakdown.completion_output = TokenBudget.estimate_tokens(str(completion_text))

        return breakdown


@dataclass
class TokenUsageRecord:
    """
    Dữ liệu ghi nhận một lượt tiêu thụ Token của một Request.
    """
    run_id: str
    thread_id: str
    user_id: Optional[str]
    input_tokens: int
    output_tokens: int
    total_tokens: int
    breakdown: TokenBreakdown
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "thread_id": self.thread_id,
            "user_id": self.user_id,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "breakdown": self.breakdown.to_dict(),
            "timestamp": self.timestamp
        }


class TokenTracker:
    """
    Bộ theo dõi và kiểm soát định mức Token theo từng Request scope.
    """
    def __init__(self, run_id: Optional[str] = None, thread_id: Optional[str] = None, user_id: Optional[str] = None):
        self.run_id = run_id or "run_unknown"
        self.thread_id = thread_id or "thread_unknown"
        self.user_id = user_id

    def track_usage(self, breakdown: TokenBreakdown) -> TokenUsageRecord:
        record = TokenUsageRecord(
            run_id=self.run_id,
            thread_id=self.thread_id,
            user_id=self.user_id,
            input_tokens=breakdown.total_input_tokens,
            output_tokens=breakdown.completion_output,
            total_tokens=breakdown.total_tokens,
            breakdown=breakdown
        )
        TokenAggregator().record_usage(record)
        return record

    @staticmethod
    def check_threshold(total_tokens: int, max_threshold: int = 4000) -> bool:
        """Cảnh báo khi số lượng Token vượt quá mốc an toàn."""
        if total_tokens > max_threshold:
            logger.warning(f"[TokenTracker] ⚠️ Token usage high! {total_tokens} > threshold {max_threshold}")
            return True
        return False


class TokenAggregator:
    """
    Bộ thống kê tổng lũy kế Token tiêu thụ của toàn hệ thống trong RAM đệm.
    """
    _instance = None

    def __new__(cls, max_samples: int = 1000):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.max_samples = max_samples
            cls._instance.records: List[TokenUsageRecord] = []
        return cls._instance

    def record_usage(self, record: TokenUsageRecord):
        if len(self.records) >= self.max_samples:
            self.records.pop(0)
        self.records.append(record)

    def get_summary(self) -> Dict[str, Any]:
        """
        Tính toán tổng lũy kế Token input, output, total và trung bình per request.
        """
        if not self.records:
            return {
                "count": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "total_tokens": 0,
                "avg_tokens_per_request": 0.0
            }

        total_in = sum(r.input_tokens for r in self.records)
        total_out = sum(r.output_tokens for r in self.records)
        total_sum = sum(r.total_tokens for r in self.records)
        count = len(self.records)

        return {
            "count": count,
            "total_input_tokens": total_in,
            "total_output_tokens": total_out,
            "total_tokens": total_sum,
            "avg_tokens_per_request": round(total_sum / count, 2)
        }

    def clear(self):
        self.records.clear()
