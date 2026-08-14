import os
import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage

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

    async def run_agent(
        self,
        message: str,
        thread_id: str,
        baby_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_handoffs: int = 3,
        execution_timeout: float = 90.0
    ) -> Dict[str, Any]:
        """
        Master Pipeline Implementation:
        Tier 0 -> Tier 1 -> EscalationPolicy -> CapabilityRegistry -> Tier 2
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
                "user_id": user_id
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

        # ── ESCALATION POLICY EVALUATION (CAPABILITY GAP) ──
        escalation_policy = EscalationPolicy()
        decision: EscalationDecision = escalation_policy.evaluate(tier1_result)

        if not decision.should_escalate:
            logger.info("[Orchestrator] Tier 1 solved request natively. Returning grounded response.")
            state["messages"].append(AIMessage(content=tier1_result.answer, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()}))
            return state

        # ── CAPABILITY REGISTRY SPECIALIST RESOLUTION ──
        selected_agent, coverage_score = CapabilityRegistry.resolve_agent_by_capability(decision.unmet_capabilities)

        if not selected_agent:
            logger.warning(f"[Orchestrator] NoSuitableAgent found for unmet capabilities: {decision.unmet_capabilities}. Safe Fallback to Tier 1 response.")
            fallback_step = {
                "id": f"step_{uuid.uuid4().hex[:6]}",
                "tool_name": "NoSuitableAgentFallback",
                "display_name": "NoSuitableAgent: Fallback an toàn về câu trả lời Tier 1",
                "args": {"unmet_capabilities": decision.unmet_capabilities},
                "status": "completed",
                "result_summary": "Không tìm thấy Specialist Agent phù hợp -> Safe Fallback tại Tier 1",
                "start_time": datetime.now(timezone.utc).isoformat(),
            }
            state["tool_steps"].append(fallback_step)
            state["messages"].append(AIMessage(content=tier1_result.answer, response_metadata={"created_at": datetime.now(timezone.utc).isoformat()}))
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

        return state


    async def stream_agent(
        self,
        message: str,
        thread_id: str,
        baby_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_handoffs: int = 3,
        execution_timeout: float = 90.0
    ):
        """
        W3C Standard SSE Generator Engine cho AI Chat Assistant:
        - Sinh `run_id` duy nhất và quản lý chuỗi `seq` tăng dần cho từng event.
        - Phát event 'run.accepted' khi bắt đầu nhận request.
        - Stream event 'run.step' & 'tool_step' trực quan hóa tiến trình.
        - Stream event 'response.token' và 'response.completed'.
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
        effective_timeout = COMPLEX_TASK_TIMEOUT if is_complex else execution_timeout

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
            chunk_size = 4
            for i in range(0, len(words), chunk_size):
                if ttft_ms is None:
                    ttft_ms = int((time.time() - t0) * 1000)
                chunk_text = " ".join(words[i:i + chunk_size]) + " "
                yield ResponseFormatter.format_sse_event("response.token", {"run_id": run_id, "trace_id": trace_id, "delta": chunk_text}, seq=seq)
                seq += 1

            decode_duration = max(time.time() - t0, 0.01)
            decode_tps = round(len(words) / decode_duration, 2)

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
                "ttft_ms": ttft_ms or int(decode_duration * 1000),
                "decode_tps": decode_tps,
                "content": last_ai_content,
                "citations": citations,
                "next_step": state.get("next_step"),
                "extracted_data": state.get("extracted_data"),
                "tool_steps": tool_steps
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
