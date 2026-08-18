import pytest
from app.AI_agents.llmops.cost.token_tracker import TokenBreakdown, TokenMetricsTracker, TokenTracker, TokenUsageRecord, TokenAggregator
from app.AI_agents.context.context_types import ContextBundle


def test_token_breakdown_schema_and_totals():
    """Verify TokenBreakdown calculates total input and total tokens."""
    breakdown = TokenBreakdown(
        system_instruction=200,
        long_term_facts=50,
        rag_docs=300,
        conversation_summary=100,
        recent_messages=150,
        completion_output=80
    )

    assert breakdown.total_input_tokens == 800
    assert breakdown.total_tokens == 880

    d = breakdown.to_dict()
    assert d["system_instruction"] == 200
    assert d["total_input_tokens"] == 800
    assert d["total_tokens"] == 880


def test_token_metrics_tracker_from_context_bundle():
    """Verify TokenMetricsTracker parses breakdown from ContextBundle."""
    bundle = ContextBundle(
        system_instruction="System prompt",
        messages=[],
        total_tokens=650,
        token_breakdown={
            "SYSTEM_INSTRUCTION": 200,
            "LONG_TERM_FACTS": 50,
            "RAG_DOCS": 300,
            "CONVERSATION_SUMMARY": 100,
            "RECENT_MESSAGES": 0
        }
    )

    breakdown = TokenMetricsTracker.from_context_bundle(bundle, completion_text="Hello parent!")
    assert breakdown.system_instruction == 200
    assert breakdown.long_term_facts == 50
    assert breakdown.rag_docs == 300
    assert breakdown.conversation_summary == 100
    assert breakdown.completion_output > 0
    assert breakdown.total_tokens > 650


def test_token_tracker_and_aggregator():
    """Verify TokenTracker records usage and TokenAggregator accumulates summary."""
    aggregator = TokenAggregator(max_samples=50)
    aggregator.clear()

    tracker = TokenTracker(run_id="run_1", thread_id="thread_1", user_id="user_1")
    breakdown = TokenBreakdown(system_instruction=100, recent_messages=200, completion_output=50)

    record = tracker.track_usage(breakdown)
    assert isinstance(record, TokenUsageRecord)
    assert record.input_tokens == 300
    assert record.output_tokens == 50
    assert record.total_tokens == 350

    # Threshold check test
    assert TokenTracker.check_threshold(record.total_tokens, max_threshold=4000) is False
    assert TokenTracker.check_threshold(5000, max_threshold=4000) is True

    # Aggregator summary test
    summary = aggregator.get_summary()
    assert summary["count"] == 1
    assert summary["total_input_tokens"] == 300
    assert summary["total_output_tokens"] == 50
    assert summary["total_tokens"] == 350
    assert summary["avg_tokens_per_request"] == 350.0

    aggregator.clear()


def test_quality_metrics_and_collector():
    """Verify QualityMetrics calculates rates and MetricsCollector accumulates stats."""
    from app.AI_agents.llmops.observability.metrics import QualityMetrics, MetricsCollector

    collector = MetricsCollector()
    collector.clear()

    # Record 10 requests: 8 success, 2 failed
    # 3 Tier 0, 5 Tier 1, 2 Tier 2
    # 4 RAG Cache Hit, 2 RAG Cache Miss
    collector.record_request(success=True, tier=0)
    collector.record_request(success=True, tier=0)
    collector.record_request(success=True, tier=0)

    collector.record_request(success=True, tier=1, rag_cache_hit=True)
    collector.record_request(success=True, tier=1, rag_cache_hit=True)
    collector.record_request(success=True, tier=1, rag_cache_hit=True)
    collector.record_request(success=True, tier=1, rag_cache_hit=True)
    collector.record_request(success=True, tier=1, rag_cache_hit=False)

    collector.record_request(success=False, tier=2, rag_cache_hit=False)
    collector.record_request(success=False, tier=2)

    m = collector.get_metrics()
    assert isinstance(m, QualityMetrics)
    assert m.total_requests == 10
    assert m.successful_requests == 8
    assert m.failed_requests == 2
    assert m.tier0_hits == 3
    assert m.tier1_solves == 5
    assert m.tier2_escalations == 2
    assert m.rag_cache_hits == 4
    assert m.rag_cache_misses == 2

    # Rates calculations
    assert m.error_rate == 20.0
    assert m.tier0_bypass_rate == 30.0
    assert m.rag_cache_hit_rate == 66.67
    assert m.escalation_rate == 20.0

    d = collector.to_dict()
    assert d["error_rate_pct"] == 20.0
    assert d["tier0_bypass_rate_pct"] == 30.0
    assert d["rag_cache_hit_rate_pct"] == 66.67
    assert d["escalation_rate_pct"] == 20.0

    collector.clear()

