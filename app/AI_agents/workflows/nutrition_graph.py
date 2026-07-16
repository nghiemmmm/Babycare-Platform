from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.tools.implementation.nutrition_tools import NutritionTrackingTool
from app.AI_agents.tools.implementation.growth_tools import GrowthTrackingTool
from app.AI_agents.knowledge.retriever import MedicalRetriever
from langchain_core.messages import AIMessage

NUTRITION_SYSTEM_PROMPT = """
Bạn là chuyên gia dinh dưỡng nhi khoa. Nhiệm vụ của bạn là:
1. Tư vấn thực đơn ăn dặm phù hợp với độ tuổi của bé.
2. Đánh giá chỉ số cân nặng và chiều cao của bé theo chuẩn WHO.
3. Đưa ra gợi ý thực phẩm bổ sung dinh dưỡng khi cần thiết.
4. Cảnh báo khi chỉ số tăng trưởng của bé bất thường.

Trả lời bằng tiếng Việt, ấm áp và dễ hiểu. Dẫn chiếu chuẩn WHO khi đề cập chỉ số phát triển.
"""

class NutritionGraph:
    """
    Subgraph xử lý các yêu cầu dinh dưỡng và tăng trưởng của bé:
    - Kiểm tra nhật ký ăn uống
    - So sánh chỉ số tăng trưởng với chuẩn WHO
    - Tư vấn thực đơn ăn dặm theo độ tuổi
    - Cảnh báo bé thiếu dinh dưỡng hoặc thừa cân
    """
    def __init__(self):
        self.reasoner = AIReasoner(model_name="gemini-2.5-flash")
        self.nutrition_tool = NutritionTrackingTool()
        self.growth_tool = GrowthTrackingTool()
        self._retriever = None  # lazy init to avoid embedding API call on startup

    @property
    def retriever(self):
        if self._retriever is None:
            self._retriever = MedicalRetriever()
        return self._retriever

    async def nutrition_advice_node(self, state: OverallState) -> dict:
        user_message = state["messages"][-1].content
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")

        nutrition_context = ""
        growth_context = ""

        if baby_id and user_id:
            # Lấy nhật ký ăn dặm gần nhất
            try:
                logs = self.nutrition_tool._run(action="get_logs", baby_id=baby_id, user_id=user_id)
                if logs:
                    recent = logs[:5]
                    nutrition_context = "Nhật ký ăn dặm gần nhất:\n" + "\n".join(
                        [f"- {r.get('food_name', 'N/A')}: {r.get('amount_g', 0)}g ({r.get('logged_at', '')[:10]})" for r in recent]
                    )
            except Exception:
                pass

            # Lấy chỉ số tăng trưởng gần nhất
            try:
                growth_logs = self.growth_tool._run(action="get_history", baby_id=baby_id, user_id=user_id)
                if growth_logs:
                    latest = growth_logs[0]
                    growth_context = f"Chỉ số gần nhất: Chiều cao {latest.get('height')}cm, Cân nặng {latest.get('weight')}kg"
            except Exception:
                pass

        # Tra cứu kiến thức dinh dưỡng nhi khoa
        rag_context = self.retriever.retrieve_context(user_message)

        full_prompt = (
            f"{user_message}\n\n"
            f"{nutrition_context}\n\n"
            f"{growth_context}\n\n"
            f"Tài liệu dinh dưỡng tham chiếu:\n{rag_context}"
        )

        try:
            response = await self.reasoner.areason(
                prompt=full_prompt,
                system_instruction=NUTRITION_SYSTEM_PROMPT
            )
        except Exception as e:
            response = f"Xin lỗi, tôi không thể xử lý câu hỏi dinh dưỡng lúc này: {str(e)}"

        return {"messages": [AIMessage(content=response)]}

    def compile(self, checkpointer=None):
        """Compile the nutrition and growth tracking subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("nutrition_advice", self.nutrition_advice_node)
        builder.add_edge(START, "nutrition_advice")
        builder.add_edge("nutrition_advice", END)
        return builder.compile(checkpointer=checkpointer)
