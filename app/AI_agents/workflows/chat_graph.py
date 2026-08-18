import asyncio
import logging
import time
import uuid
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime, timezone, date
from langgraph.graph import StateGraph, START, END
from langsmith import traceable

logger = logging.getLogger(__name__)


from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.AI_agents.memory.memory_manager import MemoryManager
from app.modules.baby.service import BabyService
from app.modules.growth_tracking.service import GrowthTrackingService
from app.shared.concurrency import run_in_threadpool
from langchain_core.messages import AIMessage
from app.AI_agents.core.constant import CHAT_SYSTEM_PROMPT_TEMPLATE

SYSTEM_PROMPT_TEMPLATE = CHAT_SYSTEM_PROMPT_TEMPLATE

class ChatGraph:
    def __init__(self):
        from app.AI_agents.core.constant import CHAT_AGENT_MODEL, CHAT_AGENT_PROVIDER
        self.reasoner = AIReasoner(model_name=CHAT_AGENT_MODEL, provider=CHAT_AGENT_PROVIDER)
        self.baby_service = BabyService()
        self.growth_service = GrowthTrackingService(self.baby_service)
        self.memory_manager = MemoryManager()

    @traceable(name="Tier1.prepare_context")
    async def prepare_context(self, state: OverallState) -> dict:
        """
        Gom và chuẩn bị ngữ cảnh gồm Hồ sơ bé (Profile) và Tri thức Y khoa RAG song song mà không tốn token gọi LLM.

        Quy trình xử lý song song (asyncio.gather):
            1. _fetch_baby_profile: Lấy thông tin ngày sinh, tháng tuổi, chiều cao, cân nặng từ Firestore.
            2. _fetch_rag: Gọi MedicalRetriever bóc tách tài liệu chuẩn WHO/Bộ Y Tế có liên quan.
            3. Context Packing: Đóng gói thành context_bundle và prep_data để tái sử dụng (Context Reuse).

        Args:
            state (OverallState): Trạng thái hội thoại chứa baby_id, current_user_id, messages, tool_steps.

        Returns:
            dict: Từ điển chứa prep_data gồm baby_name, baby_age, growth_info, rag_context, tool_steps và context_bundle.

        Raises:
            Không phát sinh ngoại lệ; tự động fallback về giá trị mặc định khi truy vấn lỗi.
        """
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")
        tool_steps = list(state.get("tool_steps", []))

        from app.AI_agents.utils.helpers import extract_user_query, build_tool_step, calculate_elapsed_ms
        user_query = extract_user_query(state)

        baby_name = "Bé"
        baby_gender = "chưa rõ"
        baby_age = "chưa rõ"
        baby_birth_date = "chưa rõ"
        growth_info = "chưa có dữ liệu"
        rag_context = ""

        async def _fetch_baby_profile():
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
            if not user_query or len(user_query.strip()) < 3:
                return ""
            try:
                from app.AI_agents.knowledge.retriever import MedicalRetriever
                retriever = MedicalRetriever()
                return await asyncio.wait_for(retriever.retrieve_context_with_plan(user_query, k=2), timeout=10.0)
            except Exception as e:
                logger.info(f"[ChatGraph] RAG retrieval skipped / timed out: {e}")
                return ""

        t_parallel_0 = time.time()
        (baby_result, history_result), rag_context = await asyncio.gather(
            _fetch_baby_profile(),
            _fetch_rag()
        )
        parallel_ms = calculate_elapsed_ms(t_parallel_0)

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
            tool_steps.append(build_tool_step(
                tool_name="BabyProfileService",
                display_name="Kiểm tra thông tin hồ sơ & chỉ số tăng trưởng bé",
                result_summary=summary_str,
                args={"baby_id": baby_id},
                duration_ms=parallel_ms
            ))

        if rag_context:
            tool_steps.append(build_tool_step(
                tool_name="MedicalRetriever",
                display_name="Tra cứu tri thức mốc phát triển & nuôi dạy con chuẩn WHO",
                result_summary="Đã nạp tài liệu RAG tri thức chuẩn WHO",
                args={"query": user_query},
                duration_ms=parallel_ms
            ))

        from app.AI_agents.context.context_builder import ContextBuilder
        from app.AI_agents.memory.long_term_memory import LongTermMemoryStore, FactExtractor

        # Extract persistent facts from user query & retrieve cross-thread facts
        memory_store = LongTermMemoryStore()
        if user_id and baby_id and user_query:
            extractor = FactExtractor(memory_store)
            extractor.extract_and_store_facts(user_id, baby_id, user_query)

        long_term_facts = memory_store.format_facts_for_context(user_id, baby_id) if (user_id and baby_id) else ""

        baby_profile_data = {
            "baby_name": baby_name,
            "baby_gender": baby_gender,
            "baby_age": baby_age,
            "baby_birth_date": baby_birth_date,
            "growth_info": growth_info
        }
        bundle = ContextBuilder.build_chat_context(
            system_template=SYSTEM_PROMPT_TEMPLATE,
            baby_profile_data=baby_profile_data,
            rag_context=rag_context,
            messages=state.get("messages", []),
            conversation_summary=state.get("conversation_summary"),
            long_term_facts=long_term_facts,
            tool_steps=tool_steps
        )

        return {
            "user_query": user_query,
            "rag_context": bundle.rag_context,
            "system_instruction": bundle.system_instruction,
            "pruned_messages": bundle.messages,
            "tool_steps": bundle.tool_steps,
            "context_bundle": bundle
        }

    async def generate_answer_from_prep(self, state: OverallState, prep_data: dict) -> str:
        """Gọi LLM sinh câu trả lời user-facing từ ngữ cảnh đã chuẩn bị trước."""
        system_instruction = prep_data.get("system_instruction", "")
        pruned_messages = prep_data.get("pruned_messages", [])
        if not pruned_messages and state.get("messages"):
            pruned_messages = self.memory_manager.prune_messages(state["messages"], limit=15)
        try:
            return await self.reasoner.areason_with_history(
                messages=pruned_messages,
                system_instruction=system_instruction
            )
        except Exception as e:
            return f"Xin lỗi, tôi gặp lỗi kết nối với máy chủ AI: {str(e)}"

    async def stream_answer_from_prep(self, state: OverallState, prep_data: dict):
        """Live stream tokens trực tiếp từ Gemini LLM theo thời gian thực."""
        system_instruction = prep_data.get("system_instruction", "")
        pruned_messages = prep_data.get("pruned_messages", [])
        if not pruned_messages and state.get("messages"):
            pruned_messages = self.memory_manager.prune_messages(state["messages"], limit=15)
        try:
            async for token in self.reasoner.astream_reason_with_history(
                messages=pruned_messages,
                system_instruction=system_instruction
            ):
                yield token
        except Exception as e:
            yield f"Xin lỗi, tôi gặp lỗi kết nối với máy chủ AI: {str(e)}"


    async def chat_node(self, state: OverallState) -> dict:
        prep_data = await self.prepare_context(state)
        response_content = await self.generate_answer_from_prep(state, prep_data)
        return {"messages": [AIMessage(content=response_content)], "tool_steps": prep_data.get("tool_steps", []), "rag_context": prep_data.get("rag_context", "")}

    def compile(self, checkpointer=None):
        """Compile the chat subgraph flow."""
        builder = StateGraph(OverallState)
        builder.add_node("chat_node", self.chat_node)
        builder.add_edge(START, "chat_node")
        builder.add_edge("chat_node", END)
        return builder.compile(checkpointer=checkpointer)

from app.AI_agents.core.contract import AgentContract, Tier1Result

@traceable(name="Tier1.assess_query_requirements")
def assess_query_requirements(user_msg: str) -> tuple[List[str], dict]:
    """
    Bóc tách yêu cầu năng lực thực tế (Concrete Capabilities) và Tín hiệu chẩn đoán (Diagnostic Signals) từ câu hỏi.

    Quy tắc nghiệp vụ:
        - Requirement -> Capability: Bóc tách dựa trên bản chất câu hỏi, tuyệt đối không hardcode tên Agent.
        - Signal 1: Yêu cầu phân tích lịch sử/biểu đồ cá nhân -> Bật requires_personal_analysis.
        - Signal 2: Yêu cầu liên miền (vừa ăn, vừa ngủ, vừa sốt, vừa sụt cân) -> Bật requires_cross_domain_reasoning.
        - Signal 3: Sốt cao, co giật, dùng thuốc -> Bật safety_sensitive và yêu cầu medical_safety_eval.
        - Signal 4: Hỏi thiết bị/review/giá bán thời gian thực -> Gán CAPABILITY_WEB_SEARCH.

    Args:
        user_msg (str): Nội dung câu hỏi thô từ người dùng.

    Returns:
        tuple[List[str], dict]: Tuple gồm (required_capabilities, diag_signals)
            - required_capabilities (List[str]): Danh sách năng lực cụ thể cần thiết.
            - diag_signals (dict): Từ điển các cờ boolean chẩn đoán (deep reasoning, safety, cross-domain...).

    Raises:
        Không phát sinh ngoại lệ; tự động trả về giá trị mặc định ['knowledge_grounded_qa'] nếu chuỗi rỗng.
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

    # Signal 3: Y tế nhạy cảm & An toàn dùng thuốc (Medical Safety & Medication Advice)
    if any(k in msg_lower for k in ["co giật", "khó thở", "tím tái", "sốt cao", "li bì", "sốt", "hapacol", "paracetamol", "dùng thuốc", "uống thuốc"]):
        diag_signals["safety_sensitive"] = True
        diag_signals["requires_specialized_tools"] = True
        req_caps.extend(["medication_history_access", "medical_safety_eval"])

    # Signal 4: Thông tin thời gian thực, sản phẩm & xu hướng (Freshness & Product Discovery)
    FRESHNESS_AND_PRODUCT_KEYWORDS = [
        "hiện nay", "mới nhất", "tốt nhất", "dùng loại nào", "dùng máy gì",
        "review", "đánh giá", "thương hiệu", "giá bán", "giá hiện tại", "đang bán",
        "máy tiệt trùng", "xe đẩy", "máy hút sữa", "nôi cũi", "ghế ăn dặm", "bình sữa"
    ]
    if any(k in msg_lower for k in FRESHNESS_AND_PRODUCT_KEYWORDS):
        diag_signals["requires_specialized_tools"] = True
        req_caps.append("CAPABILITY_WEB_SEARCH")

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

    @traceable(name="Tier1.ChatAgent.solve")
    async def solve(self, state: dict) -> Tier1Result:
        """
        Thực thi quy trình đánh giá và giải quyết First-line của Tier 1.

        Quy trình:
            1. Thu thập Context (Hồ sơ bé + RAG WHO) mà không gọi LLM sinh user answer trước (tiết kiệm token).
            2. Phân tích câu hỏi để bóc tách required_capabilities và diagnostic signals.
            3. Đóng gói vào đối tượng Tier1Result phục vụ quyết định leo thang hoặc tự sinh câu trả lời.

        Args:
            state (dict): Trạng thái hội thoại chứa messages, baby_id, current_user_id, tool_steps.

        Returns:
            Tier1Result: Đối tượng chứa đầy đủ thông tin bằng chứng RAG, cờ chẩn đoán, năng lực yêu cầu
                và reasoning_context để tái sử dụng (Context Reuse).

        Raises:
            Không phát sinh ngoại lệ; tự động fallback và trả về Tier1Result với retrieval_confidence cơ bản nếu lỗi.
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

        # 1. Thu thập Context (RAG + Profile) mà không tốn LLM generation call
        prep_data = await self.chat_graph_instance.prepare_context(state)
        rag_context = prep_data.get("rag_context", "")

        # 2. Đánh giá requirements & diagnostic signals
        req_caps, diag_signals = assess_query_requirements(user_msg)
        evidence_sufficient = bool(rag_context and "Không tìm thấy tài liệu y tế phù hợp" not in rag_context)

        return Tier1Result(

            answer="",  # Trống ban đầu, chỉ sinh nếu EscalationPolicy quyết định KHÔNG leo thang
            evidence_sufficient=evidence_sufficient,
            retrieval_confidence=0.9 if evidence_sufficient else 0.4,
            requires_deep_reasoning=diag_signals["requires_deep_reasoning"],
            requires_multi_document_synthesis=diag_signals["requires_multi_document_synthesis"],
            requires_cross_domain_reasoning=diag_signals["requires_cross_domain_reasoning"],
            requires_personal_analysis=diag_signals["requires_personal_analysis"],
            requires_specialized_tools=diag_signals["requires_specialized_tools"],
            safety_sensitive=diag_signals["safety_sensitive"],
            required_capabilities=req_caps,
            retrieved_documents=[],
            reasoning_context={
                "user_query": user_msg,
                "rag_context": rag_context,
                "tool_steps": prep_data.get("tool_steps", []),
                "baby_id": state.get("baby_id"),
                "current_user_id": state.get("current_user_id"),
                "prep_data": prep_data
            }
        )

    async def generate_native_answer(self, state: dict, tier1_result: Tier1Result) -> str:
        """Sinh câu trả lời Tier 1 native CHỈ KHI khẳng định câu hỏi KHÔNG leo thang lên Tier 2."""
        prep_data = tier1_result.reasoning_context.get("prep_data", {})
        if not prep_data:
            prep_data = await self.chat_graph_instance.prepare_context(state)
        return await self.chat_graph_instance.generate_answer_from_prep(state, prep_data)

    async def stream_native_answer(self, state: dict, tier1_result: Tier1Result):
        """Live stream câu trả lời Tier 1 native trực tiếp từ Gemini API."""
        prep_data = tier1_result.reasoning_context.get("prep_data", {})
        if not prep_data:
            prep_data = await self.chat_graph_instance.prepare_context(state)
        async for token in self.chat_graph_instance.stream_answer_from_prep(state, prep_data):
            yield token

    async def execute(self, state: dict) -> dict:

        tier1_res = await self.solve(state)
        return {"messages": [AIMessage(content=tier1_res.answer)], "tier1_result": tier1_res}


