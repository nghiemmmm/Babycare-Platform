import pytest
import asyncio
from app.AI_agents.llmops.caching.rag_cache import RAGCacheManager
from app.AI_agents.llmops.caching.embedding_cache import EmbeddingCacheManager
from app.AI_agents.llmops.caching.response_cache import AgentResponseCacheManager


def test_rag_cache_manager_hits_misses():
    """Verify RAGCacheManager stores, retrieves, and tracks hit rate."""
    RAGCacheManager.clear()

    key = RAGCacheManager.generate_key("sốt 38.5C", k=3, domain="health")
    assert RAGCacheManager.get(key) is None  # Miss 1

    RAGCacheManager.set(key, "Nội dung RAG WHO về hạ sốt")
    cached_val = RAGCacheManager.get(key)  # Hit 1
    assert cached_val == "Nội dung RAG WHO về hạ sốt"

    stats = RAGCacheManager.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate_pct"] == 50.0
    assert stats["size"] == 1

    RAGCacheManager.clear()
    empty_stats = RAGCacheManager.get_stats()
    assert empty_stats["hits"] == 0
    assert empty_stats["size"] == 0


def test_rag_cache_lru_eviction():
    """Verify RAGCacheManager evicts oldest entry when max_entries is exceeded (LRU)."""
    RAGCacheManager.clear()
    original_max = RAGCacheManager._max_entries
    RAGCacheManager._max_entries = 3

    try:
        RAGCacheManager.set("k1", "val1")
        RAGCacheManager.set("k2", "val2")
        RAGCacheManager.set("k3", "val3")

        # Access k1 to make k2 the oldest
        assert RAGCacheManager.get("k1") == "val1"

        # Insert k4 -> should evict k2
        RAGCacheManager.set("k4", "val4")

        assert RAGCacheManager.get("k2") is None
        assert RAGCacheManager.get("k1") == "val1"
        assert RAGCacheManager.get("k3") == "val3"
        assert RAGCacheManager.get("k4") == "val4"
    finally:
        RAGCacheManager._max_entries = original_max
        RAGCacheManager.clear()


def test_embedding_cache_manager():
    """Verify EmbeddingCacheManager hashes text and stores vector list."""
    EmbeddingCacheManager.clear()

    text = "Trẻ em 6 tháng tuổi"
    vector = [0.1, 0.2, 0.3, 0.4, 0.5]

    assert EmbeddingCacheManager.get(text) is None

    EmbeddingCacheManager.set(text, vector)
    cached_vec = EmbeddingCacheManager.get(text)
    assert cached_vec == vector

    EmbeddingCacheManager.clear()
    assert EmbeddingCacheManager.get(text) is None


def test_agent_response_cache_age_brackets():
    """Verify pediatric age brackets classification."""
    assert AgentResponseCacheManager.get_age_bracket(None) == "general"
    assert AgentResponseCacheManager.get_age_bracket(-1) == "general"
    assert AgentResponseCacheManager.get_age_bracket(2) == "0_3m"
    assert AgentResponseCacheManager.get_age_bracket(5) == "4_6m"
    assert AgentResponseCacheManager.get_age_bracket(10) == "7_12m"
    assert AgentResponseCacheManager.get_age_bracket(24) == "1_3y"
    assert AgentResponseCacheManager.get_age_bracket(48) == "3_5y"


def test_agent_response_cache_safety_bypass():
    """Verify safety guardrail bypass for emergency & personal data queries."""
    # Emergency Red Flags -> Must Bypass
    can_cache_1, _ = AgentResponseCacheManager.is_cacheable("Bé sốt cao co giật phải làm sao")
    assert can_cache_1 is False

    can_cache_2, _ = AgentResponseCacheManager.is_cacheable("Bé bị khó thở và tím tái")
    assert can_cache_2 is False

    # Personal Logging / Tracking -> Must Bypass
    can_cache_3, _ = AgentResponseCacheManager.is_cacheable("Bé nhà tôi vừa bú 120ml lúc 9h")
    assert can_cache_3 is False

    # General Medical / Care FAQ -> Allowed to Cache
    can_cache_4, _ = AgentResponseCacheManager.is_cacheable("Mẹo trị hăm tã cho trẻ sơ sinh hiệu quả")
    assert can_cache_4 is True


def test_agent_response_cache_flow():
    """Verify L1 Memory response caching get/set and stats."""
    AgentResponseCacheManager.clear()

    async def run_cache_test():
        query = "Lịch tiêm chủng cho trẻ 6 tháng tuổi gồm những gì?"
        AgentResponseCacheManager.delete(query, baby_age_months=6)
        AgentResponseCacheManager.delete(query, baby_age_months=24)

        payload = {
            "content": "Trẻ 6 tháng cần tiêm cúm, 6 trong 1 mũi nhắc lại nếu chưa đủ.",
            "rag_context": "WHO immunization schedule"
        }

        # Miss
        miss_res = await AgentResponseCacheManager.get_cached_response(query, baby_age_months=6)

        assert miss_res is None

        # Set
        await AgentResponseCacheManager.set_cached_response(query, payload, baby_age_months=6)

        # Hit
        hit_res = await AgentResponseCacheManager.get_cached_response(query, baby_age_months=6)
        assert hit_res is not None
        assert hit_res["content"] == payload["content"]

        # Different age bracket -> Miss (Context Isolation)
        diff_age_res = await AgentResponseCacheManager.get_cached_response(query, baby_age_months=24)
        assert diff_age_res is None

        stats = AgentResponseCacheManager.get_stats()
        assert stats["l1_hits"] >= 1

    asyncio.run(run_cache_test())

