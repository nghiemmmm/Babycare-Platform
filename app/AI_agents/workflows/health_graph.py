import asyncio
import time
from typing import Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner

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
        user_message = ""
        if state.get("messages"):
            last_msg = state["messages"][-1]
            if isinstance(last_msg, dict):
                user_message = last_msg.get("content", "")
            elif hasattr(last_msg, "content"):
                user_message = getattr(last_msg, "content", "")
            else:
                user_message = str(last_msg)
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")

        # ── 1. FAST-PATH CẢNH BÁO ĐỎ KHẨN CẤP (< 10ms, 0 LLM Call) ─────────────────────
        EMERGENCY_KEYWORDS = ["co giật", "tím tái", "khó thở", "bất tỉnh", "trợn mắt", "sốt cao 39", "sốt cao 40", "gấp"]
        msg_lower = user_message.lower()
        import time, uuid
        from datetime import datetime, timezone
        if any(k in msg_lower for k in ["co giật", "tím tái", "bất tỉnh", "trợn mắt"]):
            emergency_content = (
                "🚨 **CẢNH BÁO Y TẾ KHẨN CẤP!** 🚨\n\n"
                "Bé có dấu hiệu **CO GIẬT DO SỐT CAO**. Phụ huynh hãy giữ bình tĩnh và thực hiện ngay các bước sơ cứu sau:\n\n"
                "1. **Đặt bé nằm nghiêng sang một bên** trên bề mặt phẳng, thoáng mát để tránh sặc chất nôn.\n"
                "2. **Tuyệt đối KHÔNG nhét bất cứ thứ gì vào miệng bé** (không dùng thìa, ngón tay hay khăn).\n"
                "3. **Nới lỏng quần áo**, dùng khăn ấm lau nách, bẹn để hạ nhiệt.\n"
                "4. 🏥 **GỌI CẤP CỨU 115 HOẶC ĐƯA BÉ ĐẾN BỆNH VIỆN GẦN NHẤT NGAY LẬP TỨC!**"
            )
            return {
                "messages": [AIMessage(content=emergency_content)],
                "tool_steps": [{
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "EmergencyRedAlert",
                    "display_name": "🚨 Cảnh báo sơ cứu Y tế Khẩn cấp (< 10ms)",
                    "status": "completed",
                    "result_summary": "Phát cảnh báo Red Alert khẩn cấp",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": 5
                }]
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
            if not user_message:
                return ""
            try:
                return await run_in_threadpool(self.retriever.retrieve_context, user_message, domain="health")
            except Exception:
                return ""

        t_parallel_0 = time.time()
        (records_res, rag_context) = await asyncio.gather(
            _fetch_records(),
            _fetch_rag()
        )
        t_parallel_1 = time.time()
        parallel_ms = int((t_parallel_1 - t_parallel_0) * 1000)

        if records_res:
            baby, records = records_res
            if baby and baby.birth_date:
                birth = date.fromisoformat(baby.birth_date[:10])
                today = date.today()
                baby_age = (today.year - birth.year) * 12 + today.month - birth.month

            rec_count = len(records) if records else 0
            if records:
                recent = records[:3]
                health_context = "Lịch sử bệnh án gần nhất:\n" + "\n".join(
                    [f"- {r.get('diagnosis', 'N/A')} ({r.get('recorded_at', '')[:10]})" for r in recent]
                )
            tool_steps.append({
                "id": f"step_{uuid.uuid4().hex[:6]}",
                "tool_name": "HealthRecordsTool",
                "display_name": "Tra cứu hồ sơ y tế cho bé",
                "args": {"action": "get_records", "baby_id": baby_id},
                "status": "completed",
                "result_summary": f"Đã nạp {rec_count} hồ sơ bệnh án",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "duration_ms": parallel_ms
            })

        if rag_context:
            tool_steps.append({
                "id": f"step_{uuid.uuid4().hex[:6]}",
                "tool_name": "MedicalRetriever",
                "display_name": "Truy vấn tài liệu nhi khoa (RAG)",
                "args": {"query": user_message[:40] + "..." if len(user_message) > 40 else user_message},
                "status": "completed",
                "result_summary": "Đã trích xuất thông tin y tế chính thống",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "duration_ms": parallel_ms
            })

        full_system_instruction = (
            f"{HEALTH_SYSTEM_PROMPT}\n\n"
            f"{health_context}\n\n"
            f"Tài liệu y khoa tham chiếu:\n{rag_context}"
        )
        
        from app.AI_agents.memory.memory_manager import MemoryManager
        pruned_messages = MemoryManager().prune_messages(state.get("messages", []), limit=15)

        try:
            response = await self.reasoner.areason_with_history(
                messages=pruned_messages,
                system_instruction=full_system_instruction
            )
        except Exception as e:
            response = f"Xin lỗi, tôi không thể xử lý câu hỏi sức khỏe lúc này: {str(e)}"

        return {
            "messages": [AIMessage(content=response, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})],
            "tool_steps": tool_steps
        }

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
        return await self.execute(state)

