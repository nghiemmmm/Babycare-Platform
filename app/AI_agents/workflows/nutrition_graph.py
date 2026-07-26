from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.tools.implementation.nutrition_tools import NutritionTrackingTool
from app.AI_agents.tools.implementation.growth_tools import GrowthTrackingTool
from app.AI_agents.knowledge.retriever import MedicalRetriever
from langchain_core.messages import AIMessage
from app.AI_agents.utils.prompts import load_prompt
from app.modules.baby.service import BabyService
from datetime import date

class NutritionGraph:
    """
    Subgraph xử lý các yêu cầu dinh dưỡng và tăng trưởng của bé:
    - Kiểm tra nhật ký ăn uống
    - So sánh chỉ số tăng trưởng với chuẩn WHO
    - Tư vấn thực đơn ăn dặm theo độ tuổi
    - Cảnh báo bé thiếu dinh dưỡng hoặc thừa cân
    """
    def __init__(self):
        self.reasoner = AIReasoner()
        self.nutrition_tool = NutritionTrackingTool()
        self.growth_tool = GrowthTrackingTool()
        self.baby_service = BabyService()
        self.nutrition_prompt = load_prompt("nutrition.txt")
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
        baby_age = None

        if baby_id and user_id:
            # 1. Tính tuổi bé
            try:
                baby = self.baby_service.get_baby_by_id(baby_id, user_id)
                if baby and baby.birth_date:
                    birth = date.fromisoformat(baby.birth_date[:10])
                    today = date.today()
                    baby_age = (today.year - birth.year) * 12 + today.month - birth.month
            except Exception:
                pass

            # 2. Lấy nhật ký ăn dặm gần nhất
            try:
                logs = self.nutrition_tool._run(action="get_logs", baby_id=baby_id, user_id=user_id)
                if logs:
                    recent = logs[:5]
                    nutrition_context = "Nhật ký ăn dặm gần nhất:\n" + "\n".join(
                        [f"- {r.get('food_name', 'N/A')}: {r.get('amount_g', 0)}g ({r.get('logged_at', '')[:10]})" for r in recent]
                    )
            except Exception:
                pass

            # 3. Lấy chỉ số tăng trưởng gần nhất
            try:
                growth_logs = self.growth_tool._run(action="get_history", baby_id=baby_id, user_id=user_id)
                if growth_logs:
                    latest = growth_logs[0]
                    growth_context = f"Chỉ số gần nhất: Chiều cao {latest.get('height')}cm, Cân nặng {latest.get('weight')}kg"
            except Exception:
                pass

        # Tra cứu kiến thức dinh dưỡng nhi khoa có lọc
        metadata_filter = {"category": "nutrition"}
        if baby_age is not None:
            metadata_filter["baby_age"] = baby_age
            
        rag_context = self.retriever.retrieve_context(user_message, metadata_filter=metadata_filter)

        full_prompt = (
            f"{user_message}\n\n"
            f"{nutrition_context}\n\n"
            f"{growth_context}\n\n"
            f"Tài liệu dinh dưỡng tham chiếu:\n{rag_context}"
        )

        try:
            response = await self.reasoner.areason(
                prompt=full_prompt,
                system_instruction=self.nutrition_prompt
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
