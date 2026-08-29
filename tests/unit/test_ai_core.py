"""
Test Core AI Module: Capability Registry, Response Formatter, Citations
"""
from unittest.mock import MagicMock
from app.AI_agents.core.response_formatter import ResponseFormatter
from app.AI_agents.core.capability_registry import CapabilityRegistry
from app.AI_agents.core.constant import CRITICAL_CAPABILITIES


def test_capability_registry_evaluation():
    """Kiểm tra Capability Registry phân giải năng lực rỗng trả về None an toàn"""
    agent, score = CapabilityRegistry.resolve_agent_by_capability([])
    assert agent is None
    assert score == 0.0
    assert "medical_safety_eval" in CRITICAL_CAPABILITIES


def test_extract_citations_deduplication():
    """Kiểm tra trích xuất và khử trùng lặp nguồn tài liệu RAG"""
    doc1 = MagicMock()
    doc1.metadata = {"source": "WHO_Guideline.pdf", "page": 12}
    
    doc2 = MagicMock()
    doc2.metadata = {"source": "WHO_Guideline.pdf", "page": 12}
    
    citations = ResponseFormatter.extract_citations(docs=[doc1, doc2])
    assert len(citations) == 1
    assert "WHO_Guideline.pdf" in citations[0].title
