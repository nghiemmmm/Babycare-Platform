from typing import Dict, Any, List, Optional
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
        from app.AI_agents.core.constant import NUTRITION_AGENT_MODEL, NUTRITION_AGENT_PROVIDER
        self.reasoner = AIReasoner(model_name=NUTRITION_AGENT_MODEL, provider=NUTRITION_AGENT_PROVIDER)
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

        tool_steps = []
        import time, uuid
        from datetime import datetime, timezone

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
                t0 = time.time()
                logs = self.nutrition_tool._run(action="get_logs", baby_id=baby_id, user_id=user_id)
                t1 = time.time()
                if isinstance(logs, list) and logs:
                    recent = logs[:5]
                    nutrition_context = "Nhật ký ăn dặm gần nhất:\n" + "\n".join(
                        [f"- {r.get('food_name', 'N/A')}: {r.get('amount_g', 0)}g ({str(r.get('logged_at', ''))[:10]})" for r in recent if isinstance(r, dict)]
                    )
                tool_steps.append({
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "NutritionTrackingTool",
                    "display_name": "Tra cứu lịch sử ăn dặm & khẩu phần",
                    "args": {"action": "get_logs", "baby_id": baby_id},
                    "status": "completed",
                    "result_summary": f"Đã trích xuất {len(logs) if logs else 0} nhật ký khẩu phần",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": int((t1 - t0) * 1000)
                })
            except Exception:
                pass

            # 3. Lấy chỉ số tăng trưởng gần nhất
            try:
                t2 = time.time()
                growth_logs = self.growth_tool._run(action="get_history", baby_id=baby_id, user_id=user_id)
                t3 = time.time()
                if isinstance(growth_logs, list) and growth_logs:
                    latest = growth_logs[0]
                    if isinstance(latest, dict):
                        growth_context = f"Chỉ số gần nhất: Chiều cao {latest.get('height')}cm, Cân nặng {latest.get('weight')}kg"
                tool_steps.append({
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "GrowthTrackingTool",
                    "display_name": "Kiểm tra chỉ số phát triển chiều cao & cân nặng",
                    "args": {"action": "get_history", "baby_id": baby_id},
                    "status": "completed",
                    "result_summary": f"Đã lấy chỉ số tăng trưởng gần nhất",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": int((t3 - t2) * 1000)
                })
            except Exception:
                pass

        # ⚡ DIRECT FAST-PATH: Nếu chỉ hỏi trực tiếp chỉ số Cân nặng / Chiều cao / Độ tuổi đã có trong DB
        # Trả lời NGAY LẬP TỨC (0 LLM Call, 0 RAG Call, Phản hồi < 0.2s)
        msg_lower = user_message.lower()
        baby_name_str = f"bé {baby.name}" if (baby_id and user_id and 'baby' in locals() and baby and baby.name) else "bé"

        if "cân nặng" in msg_lower or "nặng bao" in msg_lower or "mấy kg" in msg_lower:
            if 'latest' in locals() and latest and latest.get('weight'):
                w = latest.get('weight')
                h_str = f", chiều cao {latest.get('height')}cm" if latest.get('height') else ""
                fast_reply = f"Dựa trên nhật ký đo gần nhất, {baby_name_str} hiện tại nặng {w} kg{h_str} ạ. Mẹ có cần em hỗ trợ đánh giá chỉ số này theo chuẩn WHO không ạ? 👶"
                return {"messages": [AIMessage(content=fast_reply)], "tool_steps": tool_steps}

        if "chiều cao" in msg_lower or "cao bao" in msg_lower:
            if 'latest' in locals() and latest and latest.get('height'):
                h = latest.get('height')
                w_str = f", cân nặng {latest.get('weight')}kg" if latest.get('weight') else ""
                fast_reply = f"Dựa trên nhật ký đo gần nhất, {baby_name_str} hiện tại cao {h} cm{w_str} ạ. Mẹ cần tham khảo thêm chế độ dinh dưỡng phát triển cho bé không ạ? 👶"
                return {"messages": [AIMessage(content=fast_reply)], "tool_steps": tool_steps}

        if "mấy tháng" in msg_lower or "bao nhiêu tháng" in msg_lower:
            if baby_age is not None:
                fast_reply = f"{baby_name_str} hiện tại được {baby_age} tháng tuổi ạ. Mẹ cần tham khảo thực đơn ăn dặm hay chỉ số phát triển cho độ tuổi này không ạ? 👶"
                return {"messages": [AIMessage(content=fast_reply)], "tool_steps": tool_steps}

        # Tra cứu kiến thức dinh dưỡng nhi khoa (Bypass RAG nếu là câu hỏi tra cứu chỉ số cá nhân đơn thuần)
        is_simple_profile_query = any(k in msg_lower for k in [
            "cân nặng", "nặng bao nhiêu", "chiều cao", "cao bao nhiêu", "mấy tháng", "bao nhiêu tháng", "mấy kg", "nặng bao kg"
        ])
        
        if is_simple_profile_query:
            logger.info("[NutritionGraph] Fast-path triggered: Skipping RAG for direct profile query.")
            rag_context = "Thông tin tra cứu chỉ số cá nhân của bé từ Database."
        else:
            metadata_filter = {"category": "nutrition"}
            if baby_age is not None:
                metadata_filter["baby_age"] = baby_age
                
            t4 = time.time()
            rag_context = await self.retriever.retrieve_context_with_plan(user_message, domain="nutrition")
            t5 = time.time()
            tool_steps.append({
                "id": f"step_{uuid.uuid4().hex[:6]}",
                "tool_name": "MedicalRetriever",
                "display_name": "Truy vấn tài liệu dinh dưỡng nhi khoa (RAG)",
                "args": {"query": user_message[:40]},
                "status": "completed",
                "result_summary": "Đã trích xuất hướng dẫn dinh dưỡng WHO / Nhi khoa",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "duration_ms": int((t5 - t4) * 1000)
            })

        full_system_instruction = (
            f"{self.nutrition_prompt}\n\n"
            f"{nutrition_context}\n\n"
            f"{growth_context}\n\n"
            f"Tài liệu dinh dưỡng tham chiếu:\n{rag_context}"
        )

        from app.AI_agents.memory.memory_manager import MemoryManager
        pruned_messages = MemoryManager().prune_messages(state.get("messages", []), limit=15)

        try:
            response = await self.reasoner.areason_with_history(
                messages=pruned_messages,
                system_instruction=full_system_instruction
            )
        except Exception as e:
            response = f"Xin lỗi, tôi không thể xử lý câu hỏi dinh dưỡng lúc này: {str(e)}"

        return {"messages": [AIMessage(content=response)], "tool_steps": tool_steps}

    def compile(self, checkpointer=None):
        """Compile the nutrition and growth tracking subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("nutrition_advice", self.nutrition_advice_node)
        builder.add_edge(START, "nutrition_advice")
        builder.add_edge("nutrition_advice", END)
        return builder.compile(checkpointer=checkpointer)

from app.AI_agents.core.contract import AgentContract

class NutritionAgentContract(AgentContract):
    agent_id = "nutrition_agent"
    display_name = "Nutrition & Growth Agent"
    description = "Tư vấn chế độ ăn dặm, sữa, khẩu phần dinh dưỡng và chỉ số tăng trưởng WHO."
    capabilities = [
        "feeding_history_access",
        "growth_history_access",
        "growth_nutrition_correlation",
        "temporal_pattern_analysis",
        "allergy_safety_eval"
    ]
    intents = ["check_nutrition"]

    def __init__(self):
        self.graph = NutritionGraph().compile()

    async def execute(self, state: dict) -> dict:
        return await self.graph.ainvoke(state)

    async def execute_with_context(
        self,
        query: str,
        state: dict,
        tier1_context: Dict[str, Any],
        retrieved_docs: List[Any],
        escalation_decision=None
    ) -> dict:
        state["rag_context_reused"] = True
        state["retrieved_docs"] = retrieved_docs
        return await self.graph.ainvoke(state)

