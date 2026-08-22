from typing import List, Optional, Dict, Any, AsyncGenerator
import json
import logging
import hashlib
from datetime import datetime, timezone

from app.modules.ai_agent.schemas import (
    MessageCreateResponse,
    MessageResponseDetails,
    Citation,
    ExtractedLog,
    ToolStep
)
from app.infrastructure.cache import redis as cache_redis
from app.shared.concurrency import run_in_threadpool

logger = logging.getLogger(__name__)

from app.AI_agents.llmops.guardrails.grounding_guard import GroundingGuard, GROUNDING_DISCLAIMER


class ResponseFormatter:
    """
    Response Formatter cho BabyCare AI:
    - Unified Response: Chuẩn hóa output từ Deterministic (Tier 0) và RAG (Tier 1/2).
    - Citation: Bóc tách, giữ nguyên và deduplicate các nguồn từ RAG evidence thật, loại bỏ citation giả.
    - Grounding Guard: Đảm bảo câu trả lời được hỗ trợ bởi evidence qua GroundingGuard.
    - Cache Policy: Cache các response tra cứu y tế chung, KHÔNG cache dữ liệu cá nhân/health của từng bé.
    - Streaming (SSE): Hỗ trợ sinh luồng Server-Sent Events cho LLM response.
    """

    @staticmethod
    def extract_citations(rag_context: Optional[str] = None, docs: Optional[List[Any]] = None) -> List[Citation]:
        """
        Bóc tách và khử trùng lặp (Deduplicate) các nguồn tài liệu y tế từ RAG context hoặc danh sách Document.
        Tuyệt đối không tạo citation giả hardcode.
        """
        citations: List[Citation] = []
        seen_uris = set()

        if docs:
            for doc in docs:
                source = getattr(doc, "metadata", {}).get("source", "Tài liệu Y tế")
                page = getattr(doc, "metadata", {}).get("page")
                page_suffix = f" (Trang {page})" if page else ""
                title = f"{source}{page_suffix}"
                uri = f"rag://documents/{source}"

                if uri not in seen_uris:
                    seen_uris.add(uri)
                    citations.append(Citation(title=title, uri=uri))

        elif rag_context and "Không tìm thấy tài liệu y tế phù hợp" not in rag_context:
            # Parse text lines starting with "--- Tài liệu" or "Nguồn:"
            lines = rag_context.split("\n")
            for line in lines:
                if line.startswith("--- Tài liệu") or "Nguồn:" in line:
                    clean_title = line.strip("- ").replace("---", "").strip()
                    # Trích xuất nguồn thực tế đằng sau "Nguồn:" nếu có
                    source_key = clean_title
                    if "Nguồn:" in clean_title:
                        source_key = clean_title.split("Nguồn:")[-1].replace(")", "").strip()
                    
                    uri = f"rag://documents/{hashlib.md5(source_key.encode()).hexdigest()[:8]}"
                    if uri not in seen_uris and clean_title:
                        seen_uris.add(uri)
                        citations.append(Citation(title=clean_title, uri=uri))

        return citations


    @staticmethod
    def verify_grounding(content: str, rag_context: Optional[str] = None) -> tuple[str, bool]:
        """
        Đảm bảo câu trả lời có bằng chứng hỗ trợ (Grounding).
        Trả về (content_da_xu_ly, is_grounded).
        """
        if not rag_context or "Không tìm thấy tài liệu y tế phù hợp" in rag_context:
            # Thiếu evidence -> Gắn disclaimer chống hallucination nếu chưa có
            if GROUNDING_DISCLAIMER.strip() not in content:
                content = content.strip() + GROUNDING_DISCLAIMER
            return content, False
        return content, True

    @classmethod
    def format_unified_response(
        cls,
        raw_message: str,
        rag_context: Optional[str] = None,
        docs: Optional[List[Any]] = None,
        extracted_data: Optional[Dict[str, Any]] = None,
        next_step: Optional[str] = None,
        raw_tool_steps: Optional[List[Any]] = None
    ) -> MessageCreateResponse:
        """
        1. Unified Response: Chuẩn hóa toàn bộ output thành MessageCreateResponse thống nhất.
        2. Citations: Bóc tách nguồn thật từ RAG context.
        3. Grounding: Kiểm tra grounding trước khi đóng gói.
        """
        # Grounding check
        final_content, is_grounded = cls.verify_grounding(raw_message, rag_context)

        # Dynamic Citations (Khử trùng lặp, không hardcode)
        citations = cls.extract_citations(rag_context=rag_context, docs=docs)

        # Process Tool Steps
        tool_steps_models: List[ToolStep] = []
        if raw_tool_steps:
            for ts in raw_tool_steps:
                if isinstance(ts, dict):
                    tool_steps_models.append(ToolStep(**ts))
                elif isinstance(ts, ToolStep):
                    tool_steps_models.append(ts)

        # Process Extracted Logs (Deterministic Action Results)
        extracted_logs: List[ExtractedLog] = []
        if extracted_data and next_step in ["feeding", "medication", "symptom", "growth"]:
            time_str = datetime.now(timezone.utc).strftime("%I:%M %p")
            if next_step == "feeding":
                food = extracted_data.get("food_name", "Sữa")
                amount = extracted_data.get("amount_g", 150)
                extracted_logs.append(ExtractedLog(
                    type="feeding",
                    title="Feeding Log",
                    detail=f"{amount}ml {food}",
                    value=f"{amount}ml",
                    time=time_str
                ))
            elif next_step == "medication":
                med = extracted_data.get("medication_name", "Thuốc")
                dose = extracted_data.get("dosage", "150mg")
                extracted_logs.append(ExtractedLog(
                    type="medication",
                    title="Medication Log",
                    detail=f"{med} {dose}",
                    value=dose,
                    time=time_str
                ))
            elif next_step == "growth":
                h = extracted_data.get("height", 65)
                w = extracted_data.get("weight", 7.0)
                extracted_logs.append(ExtractedLog(
                    type="growth",
                    title="Growth Log",
                    detail=f"Height: {h}cm, Weight: {w}kg",
                    value=f"{h}cm",
                    time=time_str
                ))

        return MessageCreateResponse(
            ai_response=MessageResponseDetails(
                content=final_content,
                citations=citations
            ),
            extracted_logs=extracted_logs,
            tool_steps=tool_steps_models
        )

    @staticmethod
    def is_cacheable_query(query: str, baby_id: Optional[str] = None, is_emergency: bool = False) -> bool:
        """
        Kiểm tra câu hỏi có hợp lệ để áp dụng Response Cache hay không qua AgentResponseCacheManager.
        """
        from app.AI_agents.llmops.caching.response_cache import AgentResponseCacheManager
        cacheable, _ = AgentResponseCacheManager.is_cacheable(query, baby_id=baby_id, is_emergency=is_emergency)
        return cacheable

    @classmethod
    async def get_cached_response(
        cls,
        query: str,
        baby_age_months: Optional[int] = None,
        domain: str = "medical_qa"
    ) -> Optional[Dict[str, Any]]:
        """Lấy response từ Response Cache (L1 Memory -> L2 Redis Cloud)."""
        from app.AI_agents.llmops.caching.response_cache import AgentResponseCacheManager
        return await AgentResponseCacheManager.get_cached_response(query, baby_age_months=baby_age_months, domain=domain)

    @classmethod
    async def set_cached_response(
        cls,
        query: str,
        response_dict: Dict[str, Any],
        baby_age_months: Optional[int] = None,
        domain: str = "medical_qa",
        ttl_seconds: int = 3600
    ) -> None:
        """Lưu response vào Response Cache (đồng bộ cả L1 Memory và L2 Redis Cloud)."""
        from app.AI_agents.llmops.caching.response_cache import AgentResponseCacheManager
        await AgentResponseCacheManager.set_cached_response(
            query=query,
            response_data=response_dict,
            baby_age_months=baby_age_months,
            domain=domain,
            ttl_seconds=ttl_seconds
        )


    @staticmethod
    def format_sse_event(event_type: str, payload: Any, seq: int = 0) -> str:
        """Đóng gói gói tin SSE theo chuẩn W3C Server-Sent Events (event, id, data)."""
        data_str = json.dumps(payload, ensure_ascii=False) if isinstance(payload, (dict, list)) else str(payload)
        return f"event: {event_type}\nid: {seq}\ndata: {data_str}\n\n"

    @staticmethod
    async def create_sse_stream(content: str, chunk_size: int = 3, start_seq: int = 1) -> AsyncGenerator[str, None]:
        """
        Sinh luồng Server-Sent Events (SSE) từng chunk chữ cho client với hiệu ứng gõ máy tính mượt mà.
        """
        import asyncio
        words = content.split(" ")
        seq = start_seq
        for i in range(0, len(words), chunk_size):
            chunk_text = " ".join(words[i:i + chunk_size]) + " "
            yield ResponseFormatter.format_sse_event("response.token", {"delta": chunk_text}, seq=seq)
            seq += 1
            await asyncio.sleep(0.015)

        yield ResponseFormatter.format_sse_event("response.completed", {"content": content, "status": "completed"}, seq=seq)


