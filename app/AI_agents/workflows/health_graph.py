from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.knowledge.retriever import MedicalRetriever
from langchain_core.messages import AIMessage
from app.AI_agents.core.constant import HEALTH_SYSTEM_PROMPT
from app.modules.baby.service import BabyService
from datetime import date

class HealthGraph:
    """
    Subgraph xử lý các yêu cầu liên quan đến sức khỏe của bé:
    - Tra cứu triệu chứng và lịch sử bệnh án
    - Tư vấn chăm sóc tại nhà
    - Kiểm tra an toàn thuốc
    - Cảnh báo khi cần gặp bác sĩ
    """
    def __init__(self):
        self.reasoner = AIReasoner()
        self.health_tool = HealthRecordsTool()
        self.baby_service = BabyService()
        self._retriever = None  # lazy init to avoid embedding API call on startup

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = MedicalRetriever()
        return self._retriever

    async def health_advice_node(self, state: OverallState) -> dict:
        user_message = state["messages"][-1].content
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")

        # Lấy lịch sử bệnh án gần nhất và tính tuổi bé
        health_context = ""
        baby_age = None
        tool_steps = []
        import time, uuid
        from datetime import datetime, timezone

        if baby_id and user_id:
            try:
                t0 = time.time()
                baby = self.baby_service.get_baby_by_id(baby_id, user_id)
                if baby and baby.birth_date:
                    birth = date.fromisoformat(baby.birth_date[:10])
                    today = date.today()
                    baby_age = (today.year - birth.year) * 12 + today.month - birth.month

                records = self.health_tool._run(action="get_records", baby_id=baby_id, user_id=user_id)
                t1 = time.time()
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
                    "result_summary": f"Đã trích xuất {rec_count} hồ sơ bệnh án gần nhất",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": int((t1 - t0) * 1000)
                })
            except Exception as ex:
                tool_steps.append({
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "HealthRecordsTool",
                    "display_name": "Tra cứu hồ sơ y tế cho bé",
                    "args": {"action": "get_records", "baby_id": baby_id},
                    "status": "failed",
                    "result_summary": f"Lỗi truy vấn: {str(ex)}",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                })

        # Tra cứu kiến thức y khoa RAG có kèm bộ lọc
        metadata_filter = {"category": "health"}
        if baby_age is not None:
            metadata_filter["baby_age"] = baby_age

        t2 = time.time()
        rag_context = self.retriever.retrieve_context(user_message, metadata_filter=metadata_filter)
        t3 = time.time()
        tool_steps.append({
            "id": f"step_{uuid.uuid4().hex[:6]}",
            "tool_name": "MedicalRetriever",
            "display_name": "Truy vấn tài liệu nhi khoa (RAG)",
            "args": {"query": user_message[:40] + "..." if len(user_message) > 40 else user_message},
            "status": "completed",
            "result_summary": "Đã trích xuất thông tin y tế chính thống",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int((t3 - t2) * 1000)
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

        return {"messages": [AIMessage(content=response)], "tool_steps": tool_steps}

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
    intents = ["check_health"]

    def __init__(self):
        self.graph = HealthGraph().compile()

    async def execute(self, state: dict) -> dict:
        result = await self.graph.ainvoke(state)
        
        # Check if user message requires peer hand-off to activity logging
        user_msg = state["messages"][-1].content.lower() if state.get("messages") else ""
        if any(k in user_msg for k in ["vừa uống", "đã cho uống", "vừa dùng", "vừa uống hapacol"]):
            result["hand_off_notice"] = HandOffNotice(
                target_agent_id="voice_logging_agent",
                reason="Cross-domain: Auto-logging administered medication",
                payload={"action": "medication"}
            )
        return result
