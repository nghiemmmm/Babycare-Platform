from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.tools.implementation.health_tools import HealthRecordsTool
from app.AI_agents.knowledge.retriever import MedicalRetriever
from langchain_core.messages import AIMessage

HEALTH_SYSTEM_PROMPT = """
Bạn là trợ lý nhi khoa chuyên về theo dõi sức khỏe bé. Nhiệm vụ của bạn là:
1. Xem xét triệu chứng và lịch sử bệnh án của bé.
2. Đưa ra lời khuyên chăm sóc tại nhà phù hợp.
3. Cảnh báo rõ ràng khi nào cần đưa bé đến gặp bác sĩ.
4. Kiểm tra tính an toàn của thuốc nếu được hỏi.

RÀNG BUỘC QUAN TRỌNG: Chỉ trả lời dựa trên thông tin y khoa được cung cấp trong phần "Tài liệu y khoa tham chiếu". 
Nếu tài liệu y khoa không có thông tin hoặc không liên quan đến câu hỏi, hãy nói rõ: "Tôi không tìm thấy thông tin này trong tài liệu y tế chính thức, tuy nhiên bạn có thể tham khảo ý kiến bác sĩ nhi khoa..." và không tự ý đưa ra các hướng dẫn điều trị chi tiết không có trong tài liệu.

Luôn ưu tiên sự an toàn của bé. Không chẩn đoán bệnh, chỉ tư vấn và hướng dẫn.
"""

class HealthGraph:
    """
    Subgraph xử lý các yêu cầu liên quan đến sức khỏe của bé:
    - Tra cứu triệu chứng và lịch sử bệnh án
    - Tư vấn chăm sóc tại nhà
    - Kiểm tra an toàn thuốc
    - Cảnh báo khi cần gặp bác sĩ
    """
    def __init__(self):
        self.reasoner = AIReasoner(model_name="gemini-flash-latest")
        self.health_tool = HealthRecordsTool()
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

        # Lấy lịch sử bệnh án gần nhất
        health_context = ""
        if baby_id and user_id:
            try:
                records = self.health_tool._run(action="get_records", baby_id=baby_id, user_id=user_id)
                if records:
                    recent = records[:3]
                    health_context = "Lịch sử bệnh án gần nhất:\n" + "\n".join(
                        [f"- {r.get('diagnosis', 'N/A')} ({r.get('recorded_at', '')[:10]})" for r in recent]
                    )
            except Exception:
                pass

        # Tra cứu kiến thức y khoa RAG
        rag_context = self.retriever.retrieve_context(user_message)

        full_prompt = f"{user_message}\n\n{health_context}\n\nTài liệu y khoa tham chiếu:\n{rag_context}"
        
        try:
            response = await self.reasoner.areason(
                prompt=full_prompt,
                system_instruction=HEALTH_SYSTEM_PROMPT
            )
        except Exception as e:
            response = f"Xin lỗi, tôi không thể xử lý câu hỏi sức khỏe lúc này: {str(e)}"

        return {"messages": [AIMessage(content=response)]}

    def compile(self, checkpointer=None):
        """Compile the health tracking subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("health_advice", self.health_advice_node)
        builder.add_edge(START, "health_advice")
        builder.add_edge("health_advice", END)
        return builder.compile(checkpointer=checkpointer)
