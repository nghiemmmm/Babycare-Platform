import pytest
import asyncio
import time
from app.AI_agents.llmops.observability.latency import (
    LatencyTimer,
    LatencyBreakdown,
    LatencyTracker,
    LatencyAggregator
)


def test_latency_timer_sync():
    """Verify sync context manager measures execution duration."""
    with LatencyTimer("test_sync") as timer:
        time.sleep(0.05)  # 50ms sleep

    assert timer.elapsed_ms >= 40.0
    assert timer.elapsed_ms <= 150.0


def test_latency_timer_async():
    """Verify async context manager measures async execution duration."""
    async def _run():
        async with LatencyTimer("test_async") as timer:
            await asyncio.sleep(0.05)  # 50ms sleep

        assert timer.elapsed_ms >= 40.0
        assert timer.elapsed_ms <= 150.0

    asyncio.run(_run())


def test_latency_tracker_breakdown():
    """Verify LatencyTracker records steps, TTFT, and formats breakdown."""
    tracker = LatencyTracker(run_id="run_test", trace_id="trace_test")

    tracker.start_step("tier0")
    time.sleep(0.02)
    t0_ms = tracker.end_step("tier0")
    assert t0_ms >= 15.0

    tracker.start_step("tier1_prep")
    time.sleep(0.03)
    t1_ms = tracker.end_step("tier1_prep")
    assert t1_ms >= 20.0

    tracker.record_ttft()
    assert tracker.ttft_ms is not None
    assert tracker.ttft_ms >= 40.0

    breakdown = tracker.get_breakdown()
    assert isinstance(breakdown, LatencyBreakdown)
    assert breakdown.total_ms >= 40.0
    assert breakdown.tier0_ms == t0_ms
    assert breakdown.tier1_prep_ms == t1_ms
    assert breakdown.ttft_ms == tracker.ttft_ms

    d = tracker.to_dict()
    assert "total_ms" in d
    assert "tier0_ms" in d
    assert "step_details" in d
    assert d["tier0_ms"] == t0_ms


def test_latency_aggregator_percentiles():
    """Verify LatencyAggregator calculates P50, P90, P99, Min, Max, Avg."""
    aggregator = LatencyAggregator(max_samples=100)
    aggregator.clear()

    # Record 100 sample latencies from 10ms to 1000ms
    for i in range(1, 101):
        aggregator.record(float(i * 10))

    stats = aggregator.get_percentiles()
    assert stats["count"] == 100
    assert stats["min_ms"] == 10.0
    assert stats["max_ms"] == 1000.0
    assert stats["p50_ms"] == pytest.approx(505.0, abs=10.0)
    assert stats["p90_ms"] == pytest.approx(901.0, abs=10.0)
    assert stats["p99_ms"] == pytest.approx(990.0, abs=15.0)
    assert stats["avg_ms"] == 505.0

    aggregator.clear()
    empty_stats = aggregator.get_percentiles()
    assert empty_stats["count"] == 0
    assert empty_stats["p50_ms"] == 0.0
