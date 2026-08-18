import pytest
from app.AI_agents.llmops.guardrails.grounding_guard import GroundingGuard, GROUNDING_DISCLAIMER


def test_grounding_guard_attaches_disclaimer_when_no_context():
    """Verify GroundingGuard attaches medical disclaimer when RAG context is missing."""
    raw_response = "Trẻ 6 tháng tuổi có thể tập ăn dặm bằng bột yến mạch."
    guarded = GroundingGuard.apply_grounding_guard(raw_response, rag_context=None)

    assert GROUNDING_DISCLAIMER in guarded
    assert raw_response in guarded


def test_grounding_guard_preserves_response_when_context_present():
    """Verify GroundingGuard preserves response without disclaimer when valid context is present."""
    raw_response = "Theo tài liệu WHO, hạ sốt cho trẻ bằng Paracetamol 10-15mg/kg."
    valid_context = "--- Tài liệu 1 (Nguồn: WHO Guidelines) ---\nHạ sốt cho trẻ bằng Paracetamol."

    guarded = GroundingGuard.apply_grounding_guard(raw_response, rag_context=valid_context)

    assert GROUNDING_DISCLAIMER not in guarded
    assert guarded == raw_response
