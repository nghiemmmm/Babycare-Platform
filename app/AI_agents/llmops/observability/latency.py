import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class LatencyTimer:
    """
    Timer hỗ trợ Async Context Manager, Sync Context Manager và Decorator.
    Đo đạc chính xác thời gian thực thi bằng time.perf_counter_ns() ở cấp Nanosecond.
    """
    def __init__(self, step_name: str = "operation"):
        self.step_name = step_name
        self.start_ns: int = 0
        self.end_ns: int = 0
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self.start_ns = time.perf_counter_ns()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_ns = time.perf_counter_ns()
        self.elapsed_ms = round((self.end_ns - self.start_ns) / 1_000_000, 2)

    async def __aenter__(self):
        self.start_ns = time.perf_counter_ns()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.end_ns = time.perf_counter_ns()
        self.elapsed_ms = round((self.end_ns - self.start_ns) / 1_000_000, 2)


@dataclass
class LatencyBreakdown:
    """
    Cấu trúc dữ liệu phân rã Latency chi tiết theo từng giai đoạn xử lý.
    """
    total_ms: float = 0.0
    tier0_ms: float = 0.0
    tier1_prep_ms: float = 0.0
    tier1_rag_search_ms: float = 0.0
    tier1_assessment_ms: float = 0.0
    tier1_llm_gen_ms: float = 0.0
    escalation_policy_ms: float = 0.0
    tier2_execution_ms: float = 0.0
    ttft_ms: Optional[float] = None
    step_details: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_ms": self.total_ms,
            "tier0_ms": self.tier0_ms,
            "tier1_prep_ms": self.tier1_prep_ms,
            "tier1_rag_search_ms": self.tier1_rag_search_ms,
            "tier1_assessment_ms": self.tier1_assessment_ms,
            "tier1_llm_gen_ms": self.tier1_llm_gen_ms,
            "escalation_policy_ms": self.escalation_policy_ms,
            "tier2_execution_ms": self.tier2_execution_ms,
            "ttft_ms": self.ttft_ms,
            "step_details": self.step_details
        }


class LatencyTracker:
    """
    Bộ theo dõi tích lũy mốc thời gian trong vòng đời một Request (Request Scope Tracker).
    """
    def __init__(self, run_id: Optional[str] = None, trace_id: Optional[str] = None):
        self.run_id = run_id
        self.trace_id = trace_id
        self.start_ns = time.perf_counter_ns()
        self.steps_start: Dict[str, int] = {}
        self.step_durations_ms: Dict[str, float] = {}
        self.ttft_ms: Optional[float] = None

    def start_step(self, step_name: str):
        """Bắt đầu đo một bước xử lý."""
        self.steps_start[step_name] = time.perf_counter_ns()

    def end_step(self, step_name: str) -> float:
        """Kết thúc đo bước xử lý và lưu độ trễ (ms)."""
        if step_name in self.steps_start:
            elapsed_ns = time.perf_counter_ns() - self.steps_start[step_name]
            duration_ms = round(elapsed_ns / 1_000_000, 2)
            self.step_durations_ms[step_name] = duration_ms
            return duration_ms
        return 0.0

    def record_ttft(self):
        """Ghi nhận mốc thời gian cho token đầu tiên (Time To First Token) trong chế độ Streaming."""
        if self.ttft_ms is None:
            elapsed_ns = time.perf_counter_ns() - self.start_ns
            self.ttft_ms = round(elapsed_ns / 1_000_000, 2)

    def get_breakdown(self) -> LatencyBreakdown:
        total_ns = time.perf_counter_ns() - self.start_ns
        total_ms = round(total_ns / 1_000_000, 2)

        return LatencyBreakdown(
            total_ms=total_ms,
            tier0_ms=self.step_durations_ms.get("tier0", 0.0),
            tier1_prep_ms=self.step_durations_ms.get("tier1_prep", 0.0),
            tier1_rag_search_ms=self.step_durations_ms.get("tier1_rag", 0.0),
            tier1_assessment_ms=self.step_durations_ms.get("tier1_assessment", 0.0),
            tier1_llm_gen_ms=self.step_durations_ms.get("tier1_llm_gen", 0.0),
            escalation_policy_ms=self.step_durations_ms.get("escalation_policy", 0.0),
            tier2_execution_ms=self.step_durations_ms.get("tier2_execution", 0.0),
            ttft_ms=self.ttft_ms,
            step_details=dict(self.step_durations_ms)
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.get_breakdown().to_dict()


class LatencyAggregator:
    """
    Bộ thống kê tổng hợp chỉ số hiệu năng hệ thống (P50, P90, P99 Percentiles).
    """
    _instance = None

    def __new__(cls, max_samples: int = 1000):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.max_samples = max_samples
            cls._instance.samples: List[float] = []
        return cls._instance

    def record(self, latency_ms: float):
        """Ghi nhận một mẫu độ trễ."""
        if latency_ms <= 0:
            return
        if len(self.samples) >= self.max_samples:
            self.samples.pop(0)
        self.samples.append(latency_ms)

    def get_percentiles(self) -> Dict[str, float]:
        """
        Tính toán các chỉ số thống kê P50 (Median), P90, P99, Min, Max, Average.
        """
        if not self.samples:
            return {
                "count": 0,
                "p50_ms": 0.0,
                "p90_ms": 0.0,
                "p99_ms": 0.0,
                "min_ms": 0.0,
                "max_ms": 0.0,
                "avg_ms": 0.0
            }

        sorted_s = sorted(self.samples)
        n = len(sorted_s)

        def percentile(p: float) -> float:
            k = (n - 1) * p
            f = int(k)
            c = f + 1 if f + 1 < n else f
            d = k - f
            return round(sorted_s[f] + (sorted_s[c] - sorted_s[f]) * d, 2)

        return {
            "count": n,
            "p50_ms": percentile(0.50),
            "p90_ms": percentile(0.90),
            "p99_ms": percentile(0.99),
            "min_ms": round(sorted_s[0], 2),
            "max_ms": round(sorted_s[-1], 2),
            "avg_ms": round(sum(sorted_s) / n, 2)
        }

    def clear(self):
        self.samples.clear()
