import asyncio
import time
import uuid
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone, date
from langgraph.graph import StateGraph, START, END

from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.memory.memory_manager import MemoryManager
from app.modules.baby.service import BabyService
from app.modules.growth_tracking.service import GrowthTrackingService
from app.shared.concurrency import run_in_threadpool
from langchain_core.messages import AIMessage
from app.AI_agents.core.constant import CHAT_SYSTEM_PROMPT_TEMPLATE
from datetime import datetime, timezone

SYSTEM_PROMPT_TEMPLATE = CHAT_SYSTEM_PROMPT_TEMPLATE

class ChatGraph:
    def __init__(self):
        from app.AI_agents.core.constant import CHAT_AGENT_MODEL, CHAT_AGENT_PROVIDER
        self.reasoner = AIReasoner(model_name=CHAT_AGENT_MODEL, provider=CHAT_AGENT_PROVIDER)
        self.baby_service = BabyService()
        self.growth_service = GrowthTrackingService(self.baby_service)
        self.memory_manager = MemoryManager()

    async def chat_node(self, state: OverallState) -> dict:
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")
        tool_steps = list(state.get("tool_steps", []))

        # Extract user query early (needed for parallel RAG fetch)
        user_query = ""
        if state.get("messages"):
            last_msg = state["messages"][-1]
            if isinstance(last_msg, dict):
                user_query = last_msg.get("content", "")
            elif hasattr(last_msg, "content"):
                user_query = getattr(last_msg, "content", "")
            else:
                user_query = str(last_msg)

        # ── PARALLEL: BabyProfile fetch + RAG Retrieval (tối ưu: chạy đồng thời) ──
        baby_name = "Bé"
        baby_gender = "chưa rõ"
        baby_age = "chưa rõ"
        baby_birth_date = "chưa rõ"
        growth_info = "chưa có dữ liệu"
        rag_context = ""

        async def _fetch_baby_profile():
            """Fetch BabyProfile + GrowthHistory (non-blocking via threadpool)."""
            if not (baby_id and user_id):
                return None, None
            try:
                baby, history = await asyncio.gather(
                    run_in_threadpool(self.baby_service.get_baby_by_id, baby_id, user_id),
                    run_in_threadpool(self.growth_service.get_growth_history, baby_id, user_id)
                )
                return baby, history
            except Exception:
                return None, None

        async def _fetch_rag():
            """RAG retrieval with plan (non-blocking via threadpool)."""
            if not user_query:
                return ""
            try:
                from app.AI_agents.knowledge.retriever import MedicalRetriever
                retriever = MedicalRetriever()
                return await retriever.retrieve_context_with_plan(user_query, k=2)
            except Exception:
                return ""

        t_parallel_0 = time.time()
        (baby_result, history_result), rag_context = await asyncio.gather(
            _fetch_baby_profile(),
            _fetch_rag()
        )
        t_parallel_1 = time.time()
        parallel_ms = int((t_parallel_1 - t_parallel_0) * 1000)

        # Process BabyProfile result
        if baby_result:
            baby = baby_result
            baby_name = baby.name
            baby_gender = baby.gender
            baby_birth_date = baby.birth_date
            if baby.birth_date:
                birth = date.fromisoformat(baby.birth_date[:10])
                today = date.today()
                age_months = (today.year - birth.year) * 12 + today.month - birth.month
                baby_age = str(age_months)
            if history_result:
                latest = history_result[0]
                growth_info = f"Chiều cao: {latest.height}cm, Cân nặng: {latest.weight}kg"

            summary_str = f"Đã nạp hồ sơ bé {baby_name} ({baby_age} tháng tuổi, {growth_info})"
            tool_steps.append({
                "id": f"step_{uuid.uuid4().hex[:6]}",
                "tool_name": "BabyProfileService",
                "display_name": "Kiểm tra thông tin hồ sơ & chỉ số tăng trưởng bé",
                "args": {"baby_id": baby_id},
                "status": "completed",
                "result_summary": summary_str,
                "start_time": datetime.now(timezone.utc).isoformat(),
                "duration_ms": parallel_ms
            })

        # Process RAG result
        if rag_context:
            tool_steps.append({
                "id": f"step_{uuid.uuid4().hex[:6]}",
                "tool_name": "MedicalRetriever",
                "display_name": "Tra cứu tri thức mốc phát triển & nuôi dạy con chuẩn WHO",
                "args": {"query": user_query},
                "status": "completed",
                "result_summary": "Đã nạp tài liệu RAG tri thức chuẩn WHO",
                "start_time": datetime.now(timezone.utc).isoformat(),
                "duration_ms": parallel_ms
            })

        system_instruction = SYSTEM_PROMPT_TEMPLATE.format(
            baby_name=baby_name,
            baby_gender=baby_gender,
            baby_age=baby_age,
            baby_birth_date=baby_birth_date,
            growth_info=growth_info
        )

        if rag_context:
            system_instruction += f"\n\n# TÀI LIỆU THAM CHIẾU RAG WHO:\n{rag_context}\n\n*YÊU CẦU TRÍCH DẪN: Ở cuối câu trả lời, hãy đính kèm rõ ràng một dòng: '--- Nguồn tham khảo: Tài liệu mốc phát triển & chăm sóc trẻ em chuẩn WHO'.*"

        # Prune message history to stay within context window limits (e.g. keep latest 15 messages)
        pruned_messages = self.memory_manager.prune_messages(state["messages"], limit=15)
        try:
            response_content = await self.reasoner.areason_with_history(
                messages=pruned_messages,
                system_instruction=system_instruction
            )
        except Exception as e:
            response_content = f"Xin lỗi, tôi gặp lỗi kết nối với máy chủ AI: {str(e)}"

        return {
            "messages": [AIMessage(content=response_content, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})],
            "tool_steps": tool_steps,
            "rag_context": rag_context
        }

    def compile(self, checkpointer=None):
        """Compile the chat subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("chat_node", self.chat_node)
        builder.add_edge(START, "chat_node")
        builder.add_edge("chat_node", END)
        return builder.compile(checkpointer=checkpointer)

from app.AI_agents.core.contract import AgentContract, Tier1Result

def assess_query_requirements(user_msg: str) -> tuple[List[str], dict]:
    """
    Bóc tách yêu cầu năng lực thực tế (Concrete Capabilities) và Diagnostic Signals từ câu hỏi.
    Quy tắc: Requirement -> Capability. TUYỆT ĐỐI KHÔNG mapping trực tiếp sang tên Agent.
    """
    msg_lower = user_msg.lower().strip()
    req_caps = ["knowledge_grounded_qa"]
    
    diag_signals = {
        "requires_deep_reasoning": False,
        "requires_multi_document_synthesis": False,
        "requires_cross_domain_reasoning": False,
        "requires_personal_analysis": False,
        "requires_specialized_tools": False,
        "safety_sensitive": False
    }

    # Signal 1: Yêu cầu phân tích dữ liệu cá nhân (lịch sử 14 ngày, nhật ký, biểu đồ)
    has_personal_req = any(k in msg_lower for k in [
        "lịch sử", "14 ngày", "7 ngày", "mấy ngày qua", "dạo này", "nhật ký", "biểu đồ",
        "tại sao bé tăng cân chậm", "tại sao bé lười ăn", "phân tích lịch sử"
    ])
    if has_personal_req:
        diag_signals["requires_personal_analysis"] = True
        diag_signals["requires_specialized_tools"] = True
        diag_signals["requires_deep_reasoning"] = True
        
        if any(k in msg_lower for k in ["bú", "ăn", "sữa", "tăng cân", "cân nặng", "chậm tăng"]):
            req_caps.extend(["feeding_history_access", "growth_history_access", "growth_nutrition_correlation", "temporal_pattern_analysis"])
        if any(k in msg_lower for k in ["sốt", "thuốc", "bệnh", "triệu chứng", "hapacol"]):
            req_caps.extend(["medication_history_access", "symptom_history_access", "symptom_severity_analysis", "medical_safety_eval", "temporal_pattern_analysis"])

    # Signal 2: Yêu cầu liên miền (Cross-domain)
    domains_matched = sum(1 for domain in [
        ["ăn", "bú", "sữa"],
        ["ngủ", "quấy"],
        ["cân", "cao", "tăng trưởng"],
        ["sốt", "ốm", "thuốc"]
    ] if any(w in msg_lower for w in domain))
    
    if domains_matched >= 3:
        diag_signals["requires_cross_domain_reasoning"] = True
        diag_signals["requires_deep_reasoning"] = True

    # Signal 3: Y tế nhạy cảm (Medical Safety)
    if any(k in msg_lower for k in ["co giật", "khó thở", "tím tái", "sốt cao", "li bì"]):
        diag_signals["safety_sensitive"] = True
        req_caps.append("medical_safety_eval")

    req_caps = list(dict.fromkeys(req_caps))
    return req_caps, diag_signals


class ChatAgentContract(AgentContract):
    agent_id = "chat_agent"
    display_name = "General Parenting Chat Agent & First-line Solver"
    description = "First-line Solver mặc định cho mọi thắc mắc nuôi dạy con bằng Hybrid RAG + LLM."
    capabilities = ["knowledge_grounded_qa", "general_rag_retrieval", "standard_reasoning", "multi_document_synthesis"]
    intents = ["chat"]

    def __init__(self):
        self.chat_graph_instance = ChatGraph()
        self.graph = self.chat_graph_instance.compile()

    async def solve(self, state: dict) -> Tier1Result:
        """
        Thực thi Tier 1 First-line Solver:
        1. Chạy luồng ChatGraph (RAG Retrieval + General LLM Reasoning)
        2. Đánh giá câu hỏi để xuất ra Tier1Result kèm concrete required_capabilities
        """
        user_msg = ""
        if state.get("messages"):
            last_msg = state["messages"][-1]
            if isinstance(last_msg, dict):
                user_msg = last_msg.get("content", "")
            elif hasattr(last_msg, "content"):
                user_msg = getattr(last_msg, "content", "")
            else:
                user_msg = str(last_msg)

        # 1. Thực thi Graph
        result = await self.graph.ainvoke(state)
        
        # Lấy câu trả lời sinh ra từ LLM
        messages = result.get("messages", [])
        answer_text = messages[-1].content if messages else "Xin lỗi, không có câu trả lời."
        rag_context = result.get("rag_context", "")

        # 2. Đánh giá requirements & diagnostic signals
        req_caps, diag_signals = assess_query_requirements(user_msg)
        
        evidence_sufficient = bool(rag_context and "Không tìm thấy tài liệu y tế phù hợp" not in rag_context)

        return Tier1Result(
            answer=answer_text,
            evidence_sufficient=evidence_sufficient,
            retrieval_confidence=0.9 if evidence_sufficient else 0.4,
            requires_deep_reasoning=diag_signals["requires_deep_reasoning"],
            requires_multi_document_synthesis=diag_signals["requires_multi_document_synthesis"],
            requires_cross_domain_reasoning=diag_signals["requires_cross_domain_reasoning"],
            requires_personal_analysis=diag_signals["requires_personal_analysis"],
            requires_specialized_tools=diag_signals["requires_specialized_tools"],
            safety_sensitive=diag_signals["safety_sensitive"],
            required_capabilities=req_caps,
            retrieved_documents=result.get("retrieved_docs", []),
            reasoning_context={
                "user_query": user_msg,
                "rag_context": rag_context,
                "tool_steps": result.get("tool_steps", []),
                "baby_id": state.get("baby_id"),
                "current_user_id": state.get("current_user_id")
            }
        )

    async def execute(self, state: dict) -> dict:
        tier1_res = await self.solve(state)
        return {
            "messages": [AIMessage(content=tier1_res.answer, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})],
            "tier1_result": tier1_res
        }


