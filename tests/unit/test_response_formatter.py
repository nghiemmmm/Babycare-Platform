import pytest
import asyncio
from app.AI_agents.core.response_formatter import ResponseFormatter
from app.modules.ai_agent.schemas import MessageCreateResponse

def test_unified_response_formatting():
    raw_message = "Bé 6 tháng tuổi có thể uống Hapacol 150mg khi sốt."
    rag_context = "--- Tài liệu 1 (Nguồn: WHO_Guideline.pdf | Trang 5) ---\nNội dung..."
    extracted_data = {"medication_name": "Hapacol", "dosage": "150mg"}
    next_step = "medication"

    res = ResponseFormatter.format_unified_response(
        raw_message=raw_message,
        rag_context=rag_context,
        extracted_data=extracted_data,
        next_step=next_step
    )

    assert isinstance(res, MessageCreateResponse)
    assert res.ai_response.content == raw_message
    assert len(res.ai_response.citations) > 0
    assert "WHO_Guideline.pdf" in res.ai_response.citations[0].title
    assert len(res.extracted_logs) == 1
    assert res.extracted_logs[0].type == "medication"

def test_citation_deduplication():
    rag_context = (
        "--- Tài liệu 1 (Nguồn: WHO_Guideline.pdf) ---\n"
        "--- Tài liệu 2 (Nguồn: WHO_Guideline.pdf) ---\n"
        "--- Tài liệu 3 (Nguồn: AAP_Guideline.pdf) ---"
    )
    citations = ResponseFormatter.extract_citations(rag_context=rag_context)
    # Should deduplicate duplicate sources
    sources = [c.title for c in citations]
    assert len(citations) == 2
    assert any("WHO_Guideline.pdf" in s for s in sources)
    assert any("AAP_Guideline.pdf" in s for s in sources)

def test_grounding_disclaimer():
    content = "Bé sốt nên chườm ấm."
    missing_rag = "Không tìm thấy tài liệu y tế phù hợp."

    final_content, is_grounded = ResponseFormatter.verify_grounding(content, missing_rag)
    assert is_grounded is False
    assert "Lưu ý: Chưa tìm thấy tài liệu y tế trực tiếp" in final_content

def test_cache_policy():
    # Câu hỏi cá nhân -> KHÔNG CACHE
    assert ResponseFormatter.is_cacheable_query("Con tôi bị sốt 38 độ", baby_id="baby_123") is False
    assert ResponseFormatter.is_cacheable_query("Bé Leo vừa bú 150ml", baby_id=None) is False

    # Câu hỏi chung -> CÓ CACHE
    assert ResponseFormatter.is_cacheable_query("Lịch tiêm chủng cho trẻ 6 tháng", baby_id=None) is True

def test_sse_streaming():
    async def run_stream_test():
        content = "Xin chào mẹ Minh Anh"
        chunks = []
        async for chunk in ResponseFormatter.create_sse_stream(content):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert "data:" in chunks[0]
        assert "completed" in chunks[-1]

    asyncio.run(run_stream_test())
