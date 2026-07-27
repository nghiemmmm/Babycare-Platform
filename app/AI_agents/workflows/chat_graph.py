from langgraph.graph import StateGraph, START, END
from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.memory.memory_manager import MemoryManager
from app.modules.baby.service import BabyService
from app.modules.growth_tracking.service import GrowthTrackingService
from langchain_core.messages import AIMessage
from app.AI_agents.core.constant import CHAT_SYSTEM_PROMPT_TEMPLATE

SYSTEM_PROMPT_TEMPLATE = CHAT_SYSTEM_PROMPT_TEMPLATE

class ChatGraph:
    def __init__(self):
        self.reasoner = AIReasoner()
        self.baby_service = BabyService()
        self.growth_service = GrowthTrackingService(self.baby_service)
        self.memory_manager = MemoryManager()

    async def chat_node(self, state: OverallState) -> dict:
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")
        
        baby_name = "Bé"
        baby_gender = "chưa rõ"
        baby_age = "chưa rõ"
        baby_birth_date = "chưa rõ"
        growth_info = "chưa có dữ liệu"

        if baby_id and user_id:
            try:
                baby = self.baby_service.get_baby_by_id(baby_id, user_id)
                baby_name = baby.name
                baby_gender = baby.gender
                baby_birth_date = baby.birth_date
                
                from datetime import date
                birth = date.fromisoformat(baby.birth_date[:10])
                today = date.today()
                age_months = (today.year - birth.year) * 12 + today.month - birth.month
                baby_age = str(age_months)
                
                history = self.growth_service.get_growth_history(baby_id, user_id)
                if history:
                    latest = history[0]
                    growth_info = f"Chiều cao: {latest.height}cm, Cân nặng: {latest.weight}kg vào ngày {latest.logged_at[:10]}"
            except Exception:
                pass

        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(
            baby_name=baby_name,
            baby_gender=baby_gender,
            baby_age=baby_age,
            baby_birth_date=baby_birth_date,
            growth_info=growth_info
        )

        # Prune message history to stay within context window limits (e.g. keep latest 15 messages)
        pruned_messages = self.memory_manager.prune_messages(state["messages"], limit=15)
        try:
            response_content = await self.reasoner.areason_with_history(
                messages=pruned_messages,
                system_instruction=system_instruction
            )
        except Exception as e:
            response_content = f"Xin lỗi, tôi gặp lỗi kết nối với máy chủ AI: {str(e)}"

        return {"messages": [AIMessage(content=response_content)]}

    def compile(self, checkpointer=None):
        """Compile the chat subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("chat_node", self.chat_node)
        builder.add_edge(START, "chat_node")
        builder.add_edge("chat_node", END)
        return builder.compile(checkpointer=checkpointer)
