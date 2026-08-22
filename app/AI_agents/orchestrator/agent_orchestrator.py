import os
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List, AsyncGenerator

from langchain_core.messages import HumanMessage, AIMessage
from app.core.config import settings

from app.AI_agents.orchestrator.state_manager import FirestoreCheckpointer
from app.AI_agents.core.capability_registry import CapabilityRegistry
from app.AI_agents.core.contract import HandOffNotice, Tier1Result, EscalationDecision
from app.AI_agents.orchestrator.escalation_policy import EscalationPolicy
from app.AI_agents.core.fast_extractor import FastTrackingExtractor
from app.AI_agents.workflows.health_graph import HealthAgentContract
from app.AI_agents.workflows.nutrition_graph import NutritionAgentContract
from app.AI_agents.workflows.voice_logging_graph import VoiceLoggingAgentContract, VoiceLoggingGraph
from app.AI_agents.workflows.out_of_scope_graph import OutOfScopeAgentContract
from app.AI_agents.workflows.chat_graph import ChatAgentContract
from app.AI_agents.core.response_formatter import ResponseFormatter
from app.AI_agents.llmops.observability.timeout import TimeoutConfig
from langsmith import traceable



logger = logging.getLogger(__name__)



class AgentOrchestrator:
    """
    Progressive Escalation Architecture Dispatcher for BabyCare AI.
    
    Flow:
    1. Tier 0: Fast-path (Greeting & Deterministic Read in < 50ms)
    2. Tier 1: First-line Knowledge Solver & Requirement Assessor (Hybrid RAG + LLM)
    3. EscalationPolicy: Capability Gap Evaluator (unmet = required - native)
    4. CapabilityRegistry: Specialist Coverage Resolver with Critical Constraints
    5. Tier 2: Specialized Execution Layer with Context Reuse
    """

    def __init__(self):
        self.checkpointer = FirestoreCheckpointer()
        self._initialize_registry()
        self._voice_graph = VoiceLoggingGraph()

    def _initialize_registry(self):
        """Auto-register all available AgentContracts into CapabilityRegistry."""
        if not CapabilityRegistry.get_all_agents():
            CapabilityRegistry.register(HealthAgentContract())
            CapabilityRegistry.register(NutritionAgentContract())
            CapabilityRegistry.register(VoiceLoggingAgentContract())
            CapabilityRegistry.register(OutOfScopeAgentContract(checkpointer=self.checkpointer))
            CapabilityRegistry.register(ChatAgentContract())

    @traceable(name="AgentOrchestrator.run_agent")
    async def run_agent(
        self,
        message: str,
        thread_id: str,
        baby_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_handoffs: int = 3,
        execution_timeout: float = TimeoutConfig.MASTER_EXECUTION_TIMEOUT
    ) -> Dict[str, Any]:
        """
        Thực thi luồng điều phối Master Pipeline đa tầng cho BabyCare AI.

        Quy trình xử lý tuần tự:
            1. Tier 0 Fast-Path: Pure Python Regex xử lý câu chào hỏi và tra cứu DB cơ bản (< 50ms, 0 Token).
            2. Tier 0.5 Response Caching: Kiểm tra L1 LRU / L2 Redis Cloud (< 15ms, 0 Token).
            3. Tier 1 First-line Solver: Gom ngữ cảnh (RAG WHO + Profile bé) và bóc tách required_capabilities.
            4. Escalation Policy Evaluation: So sánh Capability Gap để quyết định leo thang hay trả lời native.
            5. Capability Registry Resolution: Khớp Specialist Agent (Tier 2/Tier 3) theo Coverage Score.
            6. Specialist Execution (Context Reuse): Chuyên gia thực thi tái sử dụng ngữ cảnh từ Tier 1.
            7. Financial Observability: Tính toán độ trễ, token breakdown và chi phí ước tính USD.

        Args:
            message (str): Câu hỏi hoặc yêu cầu dạng văn bản từ phụ huynh.
            thread_id (str): ID phiên hội thoại để duy trì bộ nhớ ngắn hạn trên Firestore.
            baby_id (Optional[str]): ID hồ sơ em bé để cá nhân hóa dữ liệu y tế.
            user_id (Optional[str]): ID tài khoản phụ huynh phục vụ phân quyền bảo mật.
            max_handoffs (int): Số lần chuyển giao tối đa giữa các Agent chống lặp vô hạn (mặc định: 3).
            execution_timeout (float): Thời gian tối đa cho phép thực thi request (mặc định từ TimeoutConfig).

        Returns:
            Dict[str, Any]: Từ điển kết quả gồm messages, tool_steps, rag_context, extracted_data, financial_observability.

        Raises:
            Không làm sập ứng dụng; tự động fallback về Tier 1 grounded answer hoặc thông báo an toàn nếu gặp sự cố.
        """
        t0 = time.time()

        # ── TIER 0 FAST-PATH: Pure Code Fast Greeting & Read (< 50ms, 0 Token) ──
        fast_extracted = FastTrackingExtractor.try_extract(message)
        if fast_extracted:
            activity_type = fast_extracted.get("activity_type")
            if activity_type == "greeting":
                logger.info("[Tier 0 Fast Greeting] Phản hồi câu chào hỏi xã giao bằng Pure Code (< 30ms)!")
                baby_name = ""
                if baby_id and user_id:
                    try:
                        from app.modules.baby.service import BabyService
                        from app.shared.concurrency import run_in_threadpool
                        baby_svc = BabyService()
                        baby = await run_in_threadpool(baby_svc.get_baby_by_id, baby_id, user_id)
                        if baby and baby.name:
                            baby_name = f" cho bé {baby.name}"
                    except Exception:
                        pass
                
                greeting_content = f"Chào mẹ! Em là trợ lý BabyCare AI. Hôm nay em có thể hỗ trợ gì trong việc theo dõi sức khỏe và chăm sóc{baby_name} ạ? 💕"
                greeting_step = {
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "FastGreetingEngine",
                    "display_name": "Phản hồi câu chào nhanh (Tier 0 Fast-Path)",
                    "args": {"message": message[:40]},
                    "status": "completed",
                    "result_summary": "Đã phản hồi câu chào hỏi xã giao (< 30ms, 0 Token LLM)",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": int((time.time() - t0) * 1000)
                }
                return {
                    "messages": [AIMessage(content=greeting_content)],
                    "extracted_data": fast_extracted,
                    "next_step": "greeting",
                    "tool_steps": [greeting_step]
                }
            elif baby_id and user_id:
                logger.info(f"[Tier 0 Fast Read] Khớp câu tra cứu thông tin '{activity_type}' bằng Pure Code!")
                fast_state = {
                    "messages": [HumanMessage(content=message)],
                    "baby_id": baby_id,
                    "current_user_id": user_id,
                    "extracted_data": fast_extracted,
                    "next_step": activity_type
                }
                write_res = await self._voice_graph.write_to_db_node(fast_state)
                fast_msg = write_res.get("messages", [AIMessage(content="Đã tra cứu thông tin.")])[-1]
                fast_steps = write_res.get("tool_steps", [])

                return {
                    "messages": [fast_msg],
                    "extracted_data": fast_extracted,
                    "next_step": activity_type,
                    "tool_steps": fast_steps
                }

        from app.shared.security import mask_pii_prompt
        from app.shared.context import get_current_trace_id

        trace_id = get_current_trace_id()
        sanitized_msg = mask_pii_prompt(message)

        logger.info(f"📥 [{trace_id}] NHẬN YÊU CẦU MỚI: '{sanitized_msg}' | Thread: {thread_id} | Baby: {baby_id}")
        print(f"\n========================================================")
        print(f"📥 [{trace_id}] NHẬN CÂU HỎI MỚI TỪ UI: \"{sanitized_msg}\"")
        print(f"========================================================\n", flush=True)

        config = {
            "configurable": {
                "thread_id": thread_id,
                "baby_id": baby_id,
                "current_user_id": user_id
            }
        }
        # Load existing messages from Checkpointer if present
        checkpoint_tuple = await self.checkpointer.aget_tuple(config)
        history_messages = []
        if checkpoint_tuple and checkpoint_tuple.checkpoint:
            history_messages = checkpoint_tuple.checkpoint.get("channel_values", {}).get("messages", [])

        # Gắn created_at thật vào response_metadata ngay lúc tạo message - đây là nguồn duy
        # nhất để get_thread_messages() lọc lịch sử chat theo thời gian thực (vd. "trong vòng
        # 1 tuần"), vì HumanMessage/AIMessage không tự có timestamp.
        current_messages = list(history_messages) + [
            HumanMessage(content=message, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()})
        ]

        state: Dict[str, Any] = {
            "messages": current_messages,
            "baby_id": baby_id,
            "current_user_id": user_id,
            "tool_steps": []
        }

        # ── TIER 0.5: RESPONSE CACHING (L1 In-Memory LRU + L2 Redis Cloud < 15ms, 0 Token) ──
        try:
            cached_resp = await ResponseFormatter.get_cached_response(message)
            if cached_resp and isinstance(cached_resp, dict):
                logger.info(f"[Response Cache HIT] Trace {trace_id}: Trả kết quả cache tức thì (< 15ms)")
                cached_content = cached_resp.get("content", "")
                cached_step = {
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "ResponseCacheManager",
                    "display_name": "⚡ Phản hồi từ Bộ nhớ đệm Response Cache (< 15ms)",
                    "args": {"query": message[:50]},
                    "status": "completed",
                    "result_summary": "Phản hồi tức thì từ Cache L1/L2 (0 Token LLM tiêu thụ)",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": int((time.time() - t0) * 1000)
                }
                state["messages"].append(AIMessage(content=cached_content))
                state["tool_steps"].append(cached_step)
                state["rag_context"] = cached_resp.get("rag_context", "")
                self._attach_financial_observability(state, t0)
                return state
        except Exception as e:
            logger.warning(f"[Orchestrator] Lỗi kiểm tra Response Cache: {e}")

        # ── TIER 1: FIRST-LINE SOLVER & REQUIREMENT ASSESSMENT ──
        chat_agent = CapabilityRegistry.get_agent("chat_agent")
        if not chat_agent:
            logger.error("[Orchestrator] ChatAgent missing from registry!")
            return {"messages": [AIMessage(content="Lỗi hệ thống: Chưa khởi tạo ChatAgent.")], "tool_steps": []}

        tier1_result: Tier1Result = await chat_agent.solve(state)
        
        # Append tool_steps from Tier 1
        if tier1_result.reasoning_context and "tool_steps" in tier1_result.reasoning_context:
            state["tool_steps"].extend(tier1_result.reasoning_context["tool_steps"])
            
        state["rag_context"] = tier1_result.reasoning_context.get("rag_context", "")
        if tier1_result.reasoning_context and "prep_data" in tier1_result.reasoning_context:
            prep_data = tier1_result.reasoning_context["prep_data"]
            if "context_bundle" in prep_data:
                state["context_bundle"] = prep_data["context_bundle"]

        # ── ESCALATION POLICY EVALUATION (CAPABILITY GAP) ──
        escalation_policy = EscalationPolicy()
        decision: EscalationDecision = escalation_policy.evaluate(tier1_result)

        if not decision.should_escalate:
            logger.info("[Orchestrator] Tier 1 solved request natively. Generating grounded response.")
            native_answer = await chat_agent.generate_native_answer(state, tier1_result)
            tier1_result.answer = native_answer
            state["messages"].append(AIMessage(content=native_answer))

            # Lưu vào Response Cache nếu query hợp lệ
            if ResponseFormatter.is_cacheable_query(message, baby_id=baby_id):
                asyncio.create_task(ResponseFormatter.set_cached_response(
                    query=message,
                    response_dict={
                        "content": native_answer,
                        "rag_context": state.get("rag_context", "")
                    }
                ))

            self._attach_financial_observability(state, t0)
            return state


        # ── CAPABILITY REGISTRY SPECIALIST RESOLUTION ──
        selected_agent, coverage_score = CapabilityRegistry.resolve_agent_by_capability(decision.unmet_capabilities)

        if not selected_agent:
            logger.warning(f"[Orchestrator Tier 3] NoSuitableAgent found for unmet capabilities: {decision.unmet_capabilities}. Initiating Tier 3 Fallback Rescue Cascade...")
            
            web_enriched_answer = None
            out_of_scope_agent = CapabilityRegistry.get_agent("out_of_scope_agent")
            if out_of_scope_agent:
                try:
                    logger.info("[Orchestrator Tier 3 Rescue] Attempting OutOfScope Web Search fallback (5s timeout)...")
                    out_res = await asyncio.wait_for(
                        out_of_scope_agent.execute_with_context(
                            query=message,
                            state=state,
                            tier1_context=tier1_result.reasoning_context,
                            retrieved_docs=tier1_result.retrieved_documents,
                            escalation_decision=decision
                        ),
                        timeout=TimeoutConfig.TIER3_RESCUE_TIMEOUT
                    )
                    if out_res and out_res.get("messages"):
                        web_enriched_answer = out_res["messages"][-1].content
                except Exception as e:
                    logger.warning(f"[Orchestrator Tier 3 Rescue] OutOfScope Web Search fallback failed or timed out: {e}")

            if web_enriched_answer:
                logger.info("[Orchestrator Tier 3 Rescue] Successfully enriched answer via OutOfScope Web Search.")
                rescue_step = {
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "Tier3OutOfScopeRescue",
                    "display_name": "Tier 3 Cứu hộ: Web Search thu thập thêm thông tin mở rộng",
                    "args": {"unmet_capabilities": decision.unmet_capabilities},
                    "status": "completed",
                    "result_summary": "Đã sử dụng OutOfScope Web Search để thu thập thêm thông tin bổ sung tại Tier 3",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                }
                state["tool_steps"].append(rescue_step)
                state["messages"].append(AIMessage(content=web_enriched_answer))
            else:
                logger.info("[Orchestrator Tier 3 Safety Net] Falling back to Tier 1 native grounded response.")
                fallback_step = {
                    "id": f"step_{uuid.uuid4().hex[:6]}",
                    "tool_name": "NoSuitableAgentFallback",
                    "display_name": "Tier 3 Lưới an toàn: Fallback về câu trả lời Tier 1",
                    "args": {"unmet_capabilities": decision.unmet_capabilities},
                    "status": "completed",
                    "result_summary": "Không tìm thấy Specialist Agent phù hợp -> Safe Fallback tại Tier 1",
                    "start_time": datetime.now(timezone.utc).isoformat(),
                }
                state["tool_steps"].append(fallback_step)
                fallback_answer = await chat_agent.generate_native_answer(state, tier1_result)
                tier1_result.answer = fallback_answer
                state["messages"].append(AIMessage(content=fallback_answer))

                if ResponseFormatter.is_cacheable_query(message, baby_id=baby_id):
                    asyncio.create_task(ResponseFormatter.set_cached_response(
                        query=message,
                        response_dict={
                            "content": fallback_answer,
                            "rag_context": state.get("rag_context", "")
                        }
                    ))

            self._attach_financial_observability(state, t0)
            return state


        # ── TIER 2 SPECIALIST EXECUTION (WITH CONTEXT REUSE) ──
        logger.info(f"[Orchestrator] Escalating to '{selected_agent.agent_id}' (Coverage score: {coverage_score:.2f})")
        escalation_step = {
            "id": f"step_{uuid.uuid4().hex[:6]}",
            "tool_name": "EscalationPolicy",
            "display_name": f"Capability Escalation: Tier 1 -> {selected_agent.display_name}",
            "args": {
                "unmet_capabilities": decision.unmet_capabilities,
                "reasons": decision.reasons,
                "agent_id": selected_agent.agent_id,
                "coverage_score": coverage_score
            },
            "status": "completed",
            "result_summary": f"Chuyển giao cho {selected_agent.display_name} (Độ phủ: {int(coverage_score*100)}%)",
            "start_time": datetime.now(timezone.utc).isoformat(),
        }
        state["tool_steps"].append(escalation_step)

        tier2_result = await selected_agent.execute_with_context(
            query=message,
            state=state,
            tier1_context=tier1_result.reasoning_context,
            retrieved_docs=tier1_result.retrieved_documents,
            escalation_decision=decision
        )

        if "messages" in tier2_result and tier2_result["messages"]:
            state["messages"].extend(tier2_result["messages"])
        if "tool_steps" in tier2_result and tier2_result["tool_steps"]:
            state["tool_steps"].extend(tier2_result["tool_steps"])
        if "extracted_data" in tier2_result:
            state["extracted_data"] = tier2_result["extracted_data"]
        if "context_bundle" in tier2_result:
            state["context_bundle"] = tier2_result["context_bundle"]

        self._attach_financial_observability(state, t0)
        return state

    def _attach_financial_observability(self, state: Dict[str, Any], start_time: float):
        """Tính toán Financial Observability Metrics (Latency, Token Usage, Token Breakdown & USD Cost)."""
        from app.AI_agents.context.token_budget import TokenBudget
        elapsed_ms = int((time.time() - start_time) * 1000)

        context_bundle = state.get("context_bundle")
        token_breakdown = {}
        input_tokens = 0
        output_tokens = 0

        if context_bundle:
            if hasattr(context_bundle, "token_breakdown"):
                token_breakdown = context_bundle.token_breakdown
                input_tokens = context_bundle.total_tokens
            elif isinstance(context_bundle, dict):
                token_breakdown = context_bundle.get("token_breakdown", {})
                input_tokens = context_bundle.get("total_tokens", 0)

        if state.get("messages") and hasattr(state["messages"][-1], "content"):
            last_reply = getattr(state["messages"][-1], "content", "")
            output_tokens = TokenBudget.estimate_tokens(str(last_reply))

        total_tokens = input_tokens + output_tokens
        model_name = getattr(settings, "OPENROUTER_MODEL", "gemini-2.0-flash") or "gemini-2.0-flash"
        from app.AI_agents.llmops.observability.metrics import TokenMetricsTracker
        from app.AI_agents.llmops.cost.token_tracker import TokenTracker

        last_reply = ""
        if state.get("messages") and hasattr(state["messages"][-1], "content"):
            last_reply = getattr(state["messages"][-1], "content", "")

        parsed_breakdown = TokenMetricsTracker.from_context_bundle(context_bundle, completion_text=str(last_reply))
        tracker = TokenTracker(user_id=state.get("current_user_id"))
        usage_record = tracker.track_usage(parsed_breakdown)
        TokenTracker.check_threshold(usage_record.total_tokens)

        cost_usd = TokenBudget.calculate_cost_usd(model_name, usage_record.input_tokens, usage_record.output_tokens)

        from app.AI_agents.llmops.observability.latency import LatencyAggregator
        LatencyAggregator().record(float(elapsed_ms))

        latency_breakdown = state.get("latency_breakdown", {})
        if not latency_breakdown:
            latency_breakdown = {"total_ms": float(elapsed_ms)}

        from app.AI_agents.utils.schemas import FinancialObservabilitySchema
        obs_schema = FinancialObservabilitySchema(
            latency_ms=elapsed_ms,
            latency_breakdown=latency_breakdown,
            input_tokens=usage_record.input_tokens,
            output_tokens=usage_record.output_tokens,
            total_tokens=usage_record.total_tokens,
            token_breakdown=parsed_breakdown.to_dict(),
            estimated_cost_usd=cost_usd,
            model_name=model_name
        )
        state["financial_observability"] = obs_schema.to_dict()

    async def stream_agent(
        self,
        message: str,
        thread_id: str,
        baby_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_handoffs: int = 3,
        execution_timeout: float = TimeoutConfig.MASTER_EXECUTION_TIMEOUT
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        W3C Standard Server-Sent Events (SSE) Generator Engine cho Trợ lý Chat BabyCare AI.

        Quy trình phát sự kiện tuần tự:
            1. 'run.accepted': Xác nhận tiếp nhận request kèm run_id, trace_id.
            2. Tier 0 / Response Cache Check: Trả về kết quả tức thì nếu khớp fast-path.
            3. 'run.step' & 'tool_step': Stream trực quan hóa tiến trình suy luận và các công cụ đang chạy.
            4. 'response.token': Stream từng chunk token chữ trực tiếp tới giao diện người dùng (TTFT < 500ms).
            5. 'response.completed': Hoàn tất stream kèm dữ liệu trích xuất nhật ký và trích dẫn khoa học.

        Args:
            message (str): Câu hỏi hoặc yêu cầu dạng văn bản từ phụ huynh.
            thread_id (str): ID phiên hội thoại để quản lý bộ nhớ.
            baby_id (Optional[str]): ID hồ sơ em bé.
            user_id (Optional[str]): ID tài khoản phụ huynh.
            max_handoffs (int): Giới hạn số lần handoff tối đa (mặc định: 3).
            execution_timeout (float): Giới hạn timeout thực thi luồng stream.

        Yields:
            Dict[str, Any]: Từng SSE event được format chuẩn hóa qua ResponseFormatter (data, event, id, seq).

        Raises:
            Phát sinh event SSE 'error' hoặc thông báo fallback an toàn nếu gặp sự cố đứt kết nối/timeout.
        """
        from app.AI_agents.core.constant import COMPLEX_QUERY_KEYWORDS, COMPLEX_TASK_TIMEOUT
        from app.AI_agents.core.response_formatter import ResponseFormatter
        from app.shared.context import get_current_trace_id

        trace_id = get_current_trace_id()
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        seq = 1
        t0 = time.time()
        ttft_ms = None

        # 1. Phát event run.accepted
        yield ResponseFormatter.format_sse_event(
            "run.accepted",
            {
                "run_id": run_id,
                "trace_id": trace_id,
                "thread_id": thread_id,
                "status": "accepted",
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            seq=seq
        )
        seq += 1

        is_complex = any(k in message.lower() for k in COMPLEX_QUERY_KEYWORDS) or len(message) > 100
        effective_timeout = TimeoutConfig.COMPLEX_TASK_TIMEOUT if is_complex else execution_timeout

        # Tier 0 Fast-path Check
        fast_extracted = FastTrackingExtractor.try_extract(message)

        if fast_extracted:
            activity_type = fast_extracted.get("activity_type")
            if activity_type == "greeting":
                logger.info(f"[Tier 0 Stream Greeting] Run {run_id} | Trace {trace_id}: Phản hồi câu chào qua SSE (< 30ms)!")
                baby_name = ""
                if baby_id and user_id:
                    try:
                        from app.modules.baby.service import BabyService
                        from app.shared.concurrency import run_in_threadpool
                        baby_svc = BabyService()
                        baby = await run_in_threadpool(baby_svc.get_baby_by_id, baby_id, user_id)
                        if baby and baby.name:
                            baby_name = f" cho bé {baby.name}"
                    except Exception:
                        pass

                greeting_msg = f"Chào mẹ! Em là trợ lý BabyCare AI. Hôm nay em có thể hỗ trợ gì trong việc theo dõi sức khỏe và chăm sóc{baby_name} ạ? 💕"
                from app.AI_agents.llmops.observability.logging import ToolStepLogger, AgentExecutionLogger
                greeting_step = ToolStepLogger.create_step(
                    tool_name="FastGreetingEngine",
                    display_name="Phản hồi câu chào nhanh (Tier 0 Fast-Path)",
                    args={"message": message[:40]},
                    result_summary="Đã phản hồi câu chào hỏi xã giao (< 30ms, 0 Token LLM)",
                    duration_ms=int((time.time() - t0) * 1000)
                )

                yield ResponseFormatter.format_sse_event("run.step", {"run_id": run_id, "trace_id": trace_id, "display_name": "Tier 0 Fast Greeting"}, seq=seq)
                seq += 1
                yield ResponseFormatter.format_sse_event("tool_step", greeting_step, seq=seq)
                seq += 1

                async for chunk_event in ResponseFormatter.create_sse_stream(greeting_msg, chunk_size=3, start_seq=seq):
                    yield chunk_event
                    seq += 1

                return
            elif baby_id and user_id:
                fast_state = {
                    "messages": [HumanMessage(content=message)],
                    "baby_id": baby_id,
                    "current_user_id": user_id,
                    "extracted_data": fast_extracted,
                    "next_step": activity_type
                }
                write_res = await self._voice_graph.write_to_db_node(fast_state)
                fast_msg = write_res.get("messages", [AIMessage(content="Đã tra cứu thông tin.")])[-1].content
                fast_steps = write_res.get("tool_steps", [])

                yield ResponseFormatter.format_sse_event("run.step", {"run_id": run_id, "trace_id": trace_id, "display_name": "Tier 0 Fast Read"}, seq=seq)
                seq += 1
                for step in fast_steps:
                    yield ResponseFormatter.format_sse_event("tool_step", step, seq=seq)
                    seq += 1

                async for chunk_event in ResponseFormatter.create_sse_stream(fast_msg, chunk_size=3, start_seq=seq):
                    yield chunk_event
                    seq += 1

                return

        # 2. Redis Cache Hit Check
        try:
            cached_res = await ResponseFormatter.get_cached_response(message)
            if cached_res:
                logger.info(f"[Redis Cache HIT] Run {run_id} | Trace {trace_id}: Trả kết quả cache (< 15ms)")
                yield ResponseFormatter.format_sse_event("run.step", {"run_id": run_id, "trace_id": trace_id, "display_name": "⚡ Bộ nhớ đệm Redis Cache (< 15ms)"}, seq=seq)
                seq += 1
                cached_content = cached_res.get("content", "")
                words = cached_content.split(" ")
                for i in range(0, len(words), 5):
                    if ttft_ms is None:
                        ttft_ms = int((time.time() - t0) * 1000)
                    chunk_text = " ".join(words[i:i + 5]) + " "
                    yield ResponseFormatter.format_sse_event("response.token", {"run_id": run_id, "trace_id": trace_id, "delta": chunk_text}, seq=seq)
                    seq += 1
                    await asyncio.sleep(0.02)

                completed_payload = {
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "status": "completed",
                    "ttft_ms": ttft_ms or int((time.time() - t0) * 1000),
                    "content": cached_content,
                    "citations": cached_res.get("citations", []),
                    "extracted_data": cached_res.get("extracted_data"),
                    "tool_steps": cached_res.get("tool_steps", [])
                }
                yield ResponseFormatter.format_sse_event("response.completed", completed_payload, seq=seq)
                return
        except Exception as e:
            logger.warning(f"Lỗi kiểm tra Redis Cache: {e}")

        # 3. Stream Engine (Tier 1 / Tier 2)
        stage_desc = "🧠 Đang phân tích tác vụ phức tạp & tra cứu tri thức y tế..." if is_complex else "Bộ điều phối: Đang phân tích câu hỏi..."
        yield ResponseFormatter.format_sse_event("run.step", {"run_id": run_id, "trace_id": trace_id, "display_name": stage_desc}, seq=seq)
        seq += 1

        try:
            # 1. Khởi tạo state ngữ cảnh
            state = {
                "messages": [HumanMessage(content=message)],
                "baby_id": baby_id,
                "current_user_id": user_id,
                "handoff_count": 0,
                "tool_steps": [],
                "next_step": "chat_agent"
            }

            # 2. Thu thập ngữ cảnh & Tri thức RAG tại Tier 1 (< 0.2s)
            chat_agent = CapabilityRegistry.get_agent("chat_agent")
            if not chat_agent:
                logger.error("[Orchestrator Stream] ChatAgent missing from registry!")
                chat_agent = ChatAgentContract()

            tier1_result = await chat_agent.solve(state)
            prep_tool_steps = tier1_result.reasoning_context.get("tool_steps", [])
            state["tool_steps"].extend(prep_tool_steps)
            for step in prep_tool_steps:
                yield ResponseFormatter.format_sse_event("tool_step", step, seq=seq)
                seq += 1

            # 3. Đánh giá chính sách Leo thang (Escalation Policy)
            escalation_policy = EscalationPolicy()
            decision = escalation_policy.evaluate(tier1_result)

            if decision.should_escalate:
                logger.info(f"[Orchestrator Stream] Escalation triggered: {decision.reasons}. Chuyển giao sang Multi-Agent...")
                state = await self.run_agent(
                    message=message,
                    thread_id=thread_id,
                    baby_id=baby_id,
                    user_id=user_id,
                    max_handoffs=max_handoffs,
                    execution_timeout=effective_timeout
                )

                tool_steps = state.get("tool_steps", [])
                for step in tool_steps:
                    if step not in prep_tool_steps:
                        yield ResponseFormatter.format_sse_event("tool_step", step, seq=seq)
                        seq += 1

                last_ai_content = ""
                if state.get("messages"):
                    for m in reversed(state["messages"]):
                        if isinstance(m, AIMessage):
                            last_ai_content = m.content
                            break

                if not last_ai_content:
                    last_ai_content = "Tôi đã tiếp nhận thông tin từ bạn."

                # Stream response tokens
                words = last_ai_content.split(" ")
                chunk_size = 2
                for i in range(0, len(words), chunk_size):
                    if ttft_ms is None:
                        ttft_ms = int((time.time() - t0) * 1000)
                    chunk_text = " ".join(words[i:i + chunk_size]) + " "
                    yield ResponseFormatter.format_sse_event("response.token", {"run_id": run_id, "trace_id": trace_id, "delta": chunk_text}, seq=seq)
                    seq += 1
                    await asyncio.sleep(0.015)

                rag_ctx = state.get("rag_context", "")
                citations = ResponseFormatter.extract_citations(rag_context=rag_ctx)
                if not citations and rag_ctx:
                    citations = [{
                        "title": "Tài liệu Mốc phát triển & Chăm sóc Trẻ em chuẩn WHO",
                        "uri": "rag://who_milestones/development_guidelines"
                    }]

                end_payload = {
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "status": "completed",
                    "ttft_ms": ttft_ms or int((time.time() - t0) * 1000),
                    "content": last_ai_content,
                    "citations": citations,
                    "next_step": state.get("next_step"),
                    "extracted_data": state.get("extracted_data"),
                    "tool_steps": state.get("tool_steps", [])
                }
                yield ResponseFormatter.format_sse_event("response.completed", end_payload, seq=seq)

            else:
                # 4. Stream trực tiếp từng token từ Gemini LLM theo thời gian thực (Native Live Streaming)
                collected_tokens = []
                async for token in chat_agent.stream_native_answer(state, tier1_result):
                    if ttft_ms is None:
                        ttft_ms = int((time.time() - t0) * 1000)
                    collected_tokens.append(token)
                    yield ResponseFormatter.format_sse_event("response.token", {"run_id": run_id, "trace_id": trace_id, "delta": token}, seq=seq)
                    seq += 1


                last_ai_content = "".join(collected_tokens).strip() or "Tôi đã tiếp nhận thông tin từ bạn."
                rag_ctx = tier1_result.reasoning_context.get("rag_context", "")
                citations = ResponseFormatter.extract_citations(rag_context=rag_ctx)
                if not citations and rag_ctx:
                    citations = [{
                        "title": "Tài liệu Mốc phát triển & Chăm sóc Trẻ em chuẩn WHO",
                        "uri": "rag://who_milestones/development_guidelines"
                    }]

                end_payload = {
                    "run_id": run_id,
                    "trace_id": trace_id,
                    "status": "completed",
                    "ttft_ms": ttft_ms or int((time.time() - t0) * 1000),
                    "content": last_ai_content,
                    "citations": citations,
                    "next_step": None,
                    "extracted_data": None,
                    "tool_steps": state["tool_steps"]
                }
                try:
                    await ResponseFormatter.set_cached_response(message, end_payload)
                except Exception:
                    pass

                yield ResponseFormatter.format_sse_event("response.completed", end_payload, seq=seq)


        except Exception as ex:
            logger.error(f"[Orchestrator Stream Error] Run {run_id} | Trace {trace_id}: {ex}")

            fail_payload = {
                "run_id": run_id,
                "status": "failed",
                "error": {"code": "execution_error", "message": "Có sự gián đoạn khi trao đổi với trợ lý AI."}
            }
            yield ResponseFormatter.format_sse_event("response.failed", fail_payload, seq=seq)


    async def resume_agent(
        self,
        thread_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Legacy compatibility wrapper for resume operations."""
        return await self.run_agent(message="", thread_id=thread_id, user_id=user_id)


    async def get_state(
        self,
        thread_id: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Legacy compatibility wrapper for state retrieval."""
        config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}
        checkpoint_tuple = await self.checkpointer.aget_tuple(config)
        values = checkpoint_tuple.checkpoint.get("channel_values", {}) if checkpoint_tuple and checkpoint_tuple.checkpoint else {}
        return {
            "next": (),
            "values": values,
            "is_interrupted": False,
        }
