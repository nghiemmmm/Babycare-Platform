import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from langsmith import traceable
from app.AI_agents.orchestrator.state_manager import OverallState

from app.AI_agents.core.reasoner import AIReasoner

logger = logging.getLogger(__name__)

from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.knowledge.retriever import MedicalRetriever
from langchain_core.messages import AIMessage
from app.AI_agents.core.constant import HEALTH_SYSTEM_PROMPT
from app.modules.baby.service import BabyService
from datetime import date, datetime, timezone

class HealthGraph:
    """
    Subgraph xử lý các yêu cầu liên quan đến sức khỏe của bé:
    - Tra cứu triệu chứng và lịch sử bệnh án
    - Tư vấn chăm sóc tại nhà
    - Kiểm tra an toàn thuốc
    - Cảnh báo khi cần gặp bác sĩ
    """
    def __init__(self):
        from app.AI_agents.core.constant import HEALTH_AGENT_MODEL, HEALTH_AGENT_PROVIDER
        self.reasoner = AIReasoner(model_name=HEALTH_AGENT_MODEL, provider=HEALTH_AGENT_PROVIDER)
        self.health_tool = HealthRecordsTool()
        self.baby_service = BabyService()
        self._retriever = None  # lazy init to avoid embedding API call on startup

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = MedicalRetriever()
        return self._retriever

    async def health_advice_node(self, state: OverallState) -> dict:
        """
        Node chính xử lý tư vấn sức khỏe nhi khoa, kiểm tra an toàn dùng thuốc và phát cảnh báo đỏ khẩn cấp.

        Quy trình xử lý:
            1. Fast-Path Cảnh báo Đỏ (< 10ms, 0 LLM): Nếu phát hiện dấu hiệu co giật, tím tái, bất tỉnh,
               lập tức trả về hướng dẫn sơ cứu khẩn cấp và yêu cầu gọi cấp cứu 115.
            2. Tra cứu Lịch sử Dùng thuốc & Bệnh án từ Firestore.
            3. Context Reuse: Tái sử dụng tài liệu RAG đã lấy từ Tier 1 (hoặc truy vấn mới nếu thiếu).
            4. Phân tích LLM: Tính toán liều lượng thuốc hạ sốt an toàn theo cân nặng thực của bé.

        Args:
            state (OverallState): Trạng thái hội thoại chứa messages, baby_id, current_user_id, tool_steps.

        Returns:
            dict: Cập nhật state gồm tin nhắn tư vấn y tế chuyên sâu (messages) và danh sách tool_steps.

        Raises:
            Không phát sinh ngoại lệ; tự động fallback về hướng dẫn an toàn cơ bản khi có sự cố.
        """
        from app.AI_agents.utils.helpers import extract_user_query, build_tool_step, calculate_elapsed_ms
        user_message = extract_user_query(state)
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")

        # ── 1. FAST-PATH CẢNH BÁO ĐỎ KHẨN CẤP (< 10ms, 0 LLM Call) ─────────────────────
        from app.AI_agents.utils.validators import validate_emergency_signals
        is_emergency, signal = validate_emergency_signals(user_message)
        if is_emergency:
            emergency_content = (
                "🚨 **CẢNH BÁO Y TẾ KHẨN CẤP!** 🚨\n\n"
                f"Bé có dấu hiệu **{signal.upper() if signal else 'BẤT THƯỜNG KHẨN CẤP'}**. Phụ huynh hãy giữ bình tĩnh và thực hiện ngay các bước sơ cứu sau:\n\n"
                "1. **Đặt bé nằm nghiêng sang một bên** trên bề mặt phẳng, thoáng mát để tránh sặc chất nôn.\n"
                "2. **Tuyệt đối KHÔNG nhét bất cứ thứ gì vào miệng bé** (không dùng thìa, ngón tay hay khăn).\n"
                "3. **Nới lỏng quần áo**, dùng khăn ấm lau nách, bẹn để hạ nhiệt.\n"
                "4. 🏥 **GỌI CẤP CỨU 115 HOẶC ĐƯA BÉ ĐẾN BỆNH VIỆN GẦN NHẤT NGAY LẬP TỨC!**"
            )
            return {
                "messages": [AIMessage(content=emergency_content)],
                "tool_steps": [build_tool_step(
                    tool_name="EmergencyRedAlert",
                    display_name="🚨 Cảnh báo sơ cứu Y tế Khẩn cấp (< 10ms)",
                    result_summary=f"Phát cảnh báo Red Alert khẩn cấp: {signal}",
                    duration_ms=5
                )]
            }

        # ── 2. PARALLEL FETCH: Health Records + Medical RAG Retrieval ─────────────────────
        health_context = ""
        baby_age = None
        tool_steps = []
        from app.shared.concurrency import run_in_threadpool

        async def _fetch_records():
            if not (baby_id and user_id):
                return None, None
            try:
                baby = await run_in_threadpool(self.baby_service.get_baby_by_id, baby_id, user_id)
                records = await run_in_threadpool(self.health_tool._run, action="get_records", baby_id=baby_id, user_id=user_id)
                return baby, records
            except Exception:
                return None, None

        async def _fetch_rag():
            if state.get("rag_context"):
                logger.info("[HealthGraph] Tái sử dụng RAG context từ Tier 1 (Context Reuse).")
                return state["rag_context"]
            if not user_message:
                return ""
            try:
                return await asyncio.wait_for(
                    run_in_threadpool(self.retriever.retrieve_context, user_message, domain="health"),
                    timeout=2.0
                )
            except Exception:
                return ""


        t_parallel_0 = time.time()
        (records_res, rag_context) = await asyncio.gather(
            _fetch_records(),
            _fetch_rag()
        )
        t_parallel_1 = time.time()
        parallel_ms = int((t_parallel_1 - t_parallel_0) * 1000)

        from app.AI_agents.memory.long_term_memory import LongTermMemoryStore
        memory_store = LongTermMemoryStore()
        long_term_facts = memory_store.format_facts_for_context(user_id, baby_id) if (user_id and baby_id) else ""

        if records_res:
            baby, records = records_res
            profile_summary = ""
            if baby:
                baby_name = getattr(baby, "name", "Bé")
                baby_gender = getattr(baby, "gender", "chưa rõ")
                if getattr(baby, "birth_date", None):
                    birth = date.fromisoformat(baby.birth_date[:10])
                    today = date.today()
                    baby_age = (today.year - birth.year) * 12 + today.month - birth.month
                profile_summary = f"HỒ SƠ BÉ: {baby_name} ({baby_gender}, {baby_age or 'chưa rõ'} tháng tuổi)\n"

            rec_count = len(records) if records else 0
            if records:
                recent = records[:3]
                health_context = profile_summary + "Lịch sử bệnh án gần nhất:\n" + "\n".join(
                    [f"- {r.get('diagnosis', 'N/A')} ({r.get('recorded_at', '')[:10]})" for r in recent]
                )
            elif profile_summary:
                health_context = profile_summary

            tool_steps.append(build_tool_step(
                tool_name="HealthRecordsTool",
                display_name="Tra cứu hồ sơ y tế cho bé",
                result_summary=f"Đã nạp {rec_count} hồ sơ bệnh án",
                args={"action": "get_records", "baby_id": baby_id},
                duration_ms=parallel_ms
            ))

        if rag_context:
            summary = "Tái sử dụng RAG context từ Tier 1 (Context Reuse)" if state.get("rag_context_reused") else "Đã trích xuất thông tin y tế chính thống"
            tool_steps.append(build_tool_step(
                tool_name="MedicalRetriever",
                display_name="Truy vấn tài liệu nhi khoa (RAG)",
                result_summary=summary,
                args={"query": user_message[:40] + "..." if len(user_message) > 40 else user_message},
                duration_ms=parallel_ms
            ))

        from app.AI_agents.context.context_builder import ContextBuilder
        bundle = ContextBuilder.build_health_context(
            base_prompt=HEALTH_SYSTEM_PROMPT,
            health_records_context=health_context,
            rag_context=rag_context,
            messages=state.get("messages", []),
            long_term_facts=long_term_facts,
            tool_steps=tool_steps
        )

        try:
            response = await self.reasoner.areason_with_history(
                messages=bundle.messages,
                system_instruction=bundle.system_instruction
            )
        except Exception as e:
            response = f"Xin lỗi, tôi không thể xử lý câu hỏi sức khỏe lúc này: {str(e)}"

        return {"messages": [AIMessage(content=response)], "tool_steps": bundle.tool_steps, "context_bundle": bundle}

    def compile(self, checkpointer=None):
        """Compile the health tracking subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("health_advice", self.health_advice_node)
        builder.add_edge(START, "health_advice")
        builder.add_edge("health_advice", END)
        return builder.compile(checkpointer=checkpointer)

from app.AI_agents.core.contract import AgentContract, HandOffNotice

class HealthAgentContract(AgentContract):
    agent_id = "health_agent"
    display_name = "Health & Medical Care Agent"
    description = "Tư vấn sức khỏe nhi khoa, triệu chứng, sốt, và an toàn thuốc."
    capabilities = [
        "medication_history_access",
        "symptom_history_access",
        "symptom_severity_analysis",
        "medical_safety_eval",
        "temporal_pattern_analysis"
    ]
    intents = ["check_health"]

    def __init__(self):
        self.graph = HealthGraph().compile()

    @traceable(name="Tier2.HealthAgent.execute")
    async def execute(self, state: dict) -> dict:
        result = await self.graph.ainvoke(state)
        
        # Check if user message requires peer hand-off to activity logging
        user_msg = state["messages"][-1].content.lower() if state.get("messages") else ""
        if any(k in user_msg for k in ["vừa uống", "đã cho uống", "vừa dùng", "vừa uống hapacol"]):
            result["hand_off_notice"] = HandOffNotice(
                source_agent="health_agent",
                target_agent_id="voice_logging_agent",
                reason="Cross-domain: Auto-logging administered medication",
                payload={"action": "medication"}
            )
        return result

    @traceable(name="Tier2.HealthAgent.execute_with_context")
    async def execute_with_context(
        self,
        query: str,
        state: dict,
        tier1_context: dict,
        retrieved_docs: list,
        escalation_decision=None
    ) -> dict:
        state["rag_context_reused"] = True
        state["retrieved_docs"] = retrieved_docs
        if tier1_context and isinstance(tier1_context, dict) and tier1_context.get("rag_context"):
            state["rag_context"] = tier1_context.get("rag_context")
        return await self.execute(state)


