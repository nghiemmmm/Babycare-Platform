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
        if baby_id and user_id:
            try:
                # 1. Lấy thông tin bé để tính tuổi
                baby = self.baby_service.get_baby_by_id(baby_id, user_id)
                if baby and baby.birth_date:
                    birth = date.fromisoformat(baby.birth_date[:10])
                    today = date.today()
                    baby_age = (today.year - birth.year) * 12 + today.month - birth.month

                # 2. Lấy bệnh án gần nhất
                records = self.health_tool._run(action="get_records", baby_id=baby_id, user_id=user_id)
                if records:
                    recent = records[:3]
                    health_context = "Lịch sử bệnh án gần nhất:\n" + "\n".join(
                        [f"- {r.get('diagnosis', 'N/A')} ({r.get('recorded_at', '')[:10]})" for r in recent]
                    )
            except Exception:
                pass

        # Tra cứu kiến thức y khoa RAG có kèm bộ lọc
        metadata_filter = {"category": "health"}
        if baby_age is not None:
            metadata_filter["baby_age"] = baby_age
            
        rag_context = self.retriever.retrieve_context(user_message, metadata_filter=metadata_filter)

        full_prompt = f"{user_message}\n\n{health_context}\n\nTài liệu y khoa tham chiếu:\n{rag_context}"
        
        try:
            response = await self.reasoner.areason(
                prompt=full_prompt,
                system_instruction=HEALTH_SYSTEM_PROMPT
            )
        except Exception as e:
            response = f"Xin lỗi, tôi không thể xử lý câu hỏi sức khỏe lúc này: {str(e)}"

        return {"messages": [AIMessage(content=response, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})]}

    def compile(self, checkpointer=None):
        """Compile the health tracking subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("health_advice", self.health_advice_node)
        builder.add_edge(START, "health_advice")
        builder.add_edge("health_advice", END)
        return builder.compile(checkpointer=checkpointer)
