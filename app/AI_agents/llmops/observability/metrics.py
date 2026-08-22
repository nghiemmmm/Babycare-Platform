from typing import Dict, Any, Optional
from dataclasses import dataclass, field
import logging

from app.AI_agents.llmops.cost.token_tracker import TokenBreakdown, TokenMetricsTracker
from app.AI_agents.llmops.observability.tracing import LangSmithTracerManager, get_tracer_callbacks
from app.AI_agents.llmops.observability.logging import ToolStepLogger, AgentExecutionLogger

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """
    Schema các chỉ số vận hành & chất lượng hệ thống (Operational & Quality Metrics).
    """
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    tier0_hits: int = 0
    tier1_solves: int = 0
    tier2_escalations: int = 0
    rag_cache_hits: int = 0
    rag_cache_misses: int = 0

    @property
    def error_rate(self) -> float:
        """Tỷ lệ lỗi hệ thống (%)"""
        if self.total_requests == 0:
            return 0.0
        return round((self.failed_requests / self.total_requests) * 100, 2)

    @property
    def tier0_bypass_rate(self) -> float:
        """Tỷ lệ đi tắt Tier 0 Fast-Path (%)"""
        if self.total_requests == 0:
            return 0.0
        return round((self.tier0_hits / self.total_requests) * 100, 2)

    @property
    def rag_cache_hit_rate(self) -> float:
        """Tỷ lệ trúng RAG Result Cache (%)"""
        total_rag = self.rag_cache_hits + self.rag_cache_misses
        if total_rag == 0:
            return 0.0
        return round((self.rag_cache_hits / total_rag) * 100, 2)

    @property
    def escalation_rate(self) -> float:
        """Tỷ lệ chuyển giao (Escalate) sang Tier 2 Specialist (%)"""
        if self.total_requests == 0:
            return 0.0
        return round((self.tier2_escalations / self.total_requests) * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "tier0_hits": self.tier0_hits,
            "tier1_solves": self.tier1_solves,
            "tier2_escalations": self.tier2_escalations,
            "rag_cache_hits": self.rag_cache_hits,
            "rag_cache_misses": self.rag_cache_misses,
            "error_rate_pct": self.error_rate,
            "tier0_bypass_rate_pct": self.tier0_bypass_rate,
            "rag_cache_hit_rate_pct": self.rag_cache_hit_rate,
            "escalation_rate_pct": self.escalation_rate
        }


class MetricsCollector:
    """
    Bộ thu thập và thống kê tổng hợp chỉ số chất lượng hệ thống (Singleton RAM Counter).
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.metrics = QualityMetrics()
        return cls._instance

    def record_request(
        self,
        success: bool = True,
        tier: int = 1,
        rag_cache_hit: Optional[bool] = None
    ):
        """Ghi nhận thông số từ 1 request xử lý."""
        self.metrics.total_requests += 1

        if success:
            self.metrics.successful_requests += 1
        else:
            self.metrics.failed_requests += 1

        if tier == 0:
            self.metrics.tier0_hits += 1
        elif tier == 1:
            self.metrics.tier1_solves += 1
        elif tier == 2:
            self.metrics.tier2_escalations += 1

        if rag_cache_hit is True:
            self.metrics.rag_cache_hits += 1
        elif rag_cache_hit is False:
            self.metrics.rag_cache_misses += 1

    def get_metrics(self) -> QualityMetrics:
        return self.metrics

    def to_dict(self) -> Dict[str, Any]:
        return self.metrics.to_dict()

    def clear(self):
        self.metrics = QualityMetrics()
