import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

from langchain_core.messages import HumanMessage, AIMessage

from app.AI_agents.orchestrator.state_manager import FirestoreCheckpointer
from app.AI_agents.core.capability_registry import CapabilityRegistry
from app.AI_agents.core.contract import HandOffNotice
from app.AI_agents.workflows.health_graph import HealthAgentContract
from app.AI_agents.workflows.nutrition_graph import NutritionAgentContract
from app.AI_agents.workflows.voice_logging_graph import VoiceLoggingAgentContract
from app.AI_agents.workflows.out_of_scope_graph import OutOfScopeAgentContract
from app.AI_agents.workflows.chat_graph import ChatAgentContract

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """
    Minimal Runtime Dispatcher for BabyCare AI.
    
    Responsibilities:
    1. Infrastructure & Flow Control (request dispatching, timeout, retry, hand-off limit, fallback).
    2. Uses CapabilityRegistry to dispatch user requests to the appropriate AgentContract.
    3. Handles Peer-to-Peer Agent Hand-offs with loop protection (max_handoffs, visited_agents, timeout).
    """

    def __init__(self):
        self.checkpointer = FirestoreCheckpointer()
        self._initialize_registry()

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
        execution_timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Minimal Runtime Dispatcher Execution Loop:
        - Dispatcher selects initial agent from CapabilityRegistry.
        - Executes initial agent and manages peer hand-offs with loop safeguards.
        - Enforces max_handoffs limit, visited_agents tracking, and execution_timeout.
        """
        t0 = time.time()
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

        current_messages = list(history_messages) + [HumanMessage(content=message)]

        state: Dict[str, Any] = {
            "messages": current_messages,
            "baby_id": baby_id,
            "current_user_id": user_id,
            "tool_steps": []
        }

        # 1. Dispatcher evaluates intent using Shared CapabilityRegistry
        target_agent_id, confidence = CapabilityRegistry.evaluate_intent(message, state)
        logger.info(f"[Dispatcher] Evaluated initial target agent: '{target_agent_id}' (confidence: {confidence})")

        # Record Dispatcher Step
        dispatcher_step = {
            "id": f"step_{uuid.uuid4().hex[:6]}",
            "tool_name": "RuntimeDispatcher",
            "display_name": "Runtime Dispatcher & Capability Registry",
            "args": {"message": message[:40], "confidence": confidence},
            "status": "completed",
            "result_summary": f"Đã định hướng sang {target_agent_id} (Độ tự tin: {int(confidence*100)}%)",
            "start_time": datetime.now(timezone.utc).isoformat(),
            "duration_ms": int((time.time() - t0) * 1000)
        }
        state["tool_steps"].append(dispatcher_step)

        # Loop protection & Guardrails
        visited_agents: List[str] = []
        handoff_count = 0

        async def _execute_loop():
            nonlocal target_agent_id, handoff_count, state
            while target_agent_id and handoff_count < max_handoffs:
                if target_agent_id in visited_agents:
                    logger.warning(f"[Dispatcher] Loop detected! Agent '{target_agent_id}' already visited. Breaking hand-off loop.")
                    break

                agent = CapabilityRegistry.get_agent(target_agent_id)
                if not agent:
                    logger.warning(f"[Dispatcher] Agent '{target_agent_id}' not found in registry. Falling back to chat_agent.")
                    agent = CapabilityRegistry.get_agent("chat_agent")

                visited_agents.append(target_agent_id)
                logger.info(f"[Dispatcher] Executing agent '{agent.agent_id}' (step {handoff_count + 1})")

                try:
                    result = await agent.execute(state)
                    # Merge state
                    if "messages" in result and result["messages"]:
                        state["messages"].extend(result["messages"])
                    if "tool_steps" in result and result["tool_steps"]:
                        state["tool_steps"].extend(result["tool_steps"])
                    if "extracted_data" in result:
                        state["extracted_data"] = result["extracted_data"]
                    if "next_step" in result:
                        state["next_step"] = result["next_step"]

                    # Check for Peer Hand-off Notice
                    notice = result.get("hand_off_notice")
                    if isinstance(notice, HandOffNotice) and notice.target_agent_id != target_agent_id:
                        logger.info(f"[Dispatcher] Peer Hand-off triggered from '{target_agent_id}' -> '{notice.target_agent_id}'. Reason: {notice.reason}")
                        
                        handoff_step = {
                            "id": f"step_{uuid.uuid4().hex[:6]}",
                            "tool_name": "PeerHandOff",
                            "display_name": f"Peer Hand-off: {agent.display_name} -> {notice.target_agent_id}",
                            "args": {"reason": notice.reason},
                            "status": "completed",
                            "result_summary": f"Chuyển giao xử lý: {notice.reason}",
                            "start_time": datetime.now(timezone.utc).isoformat(),
                        }
                        state["tool_steps"].append(handoff_step)

                        target_agent_id = notice.target_agent_id
                        handoff_count += 1
                    else:
                        break
                except Exception as ex:
                    logger.error(f"[Dispatcher] Error executing agent '{target_agent_id}': {ex}")
                    state["error_message"] = str(ex)
                    break

        try:
            await asyncio.wait_for(_execute_loop(), timeout=execution_timeout)
        except asyncio.TimeoutError:
            logger.error(f"[Dispatcher] Execution timeout after {execution_timeout}s")
            state["error_message"] = f"Execution timed out after {execution_timeout}s"
            if not state.get("messages") or isinstance(state["messages"][-1], HumanMessage):
                state["messages"].append(AIMessage(content="Xin lỗi, hệ thống phản hồi quá thời gian cho phép. Vui lòng thử lại."))

        # Final Fallback check if no AIMessage generated
        if not state.get("messages") or isinstance(state["messages"][-1], HumanMessage):
            chat_agent = CapabilityRegistry.get_agent("chat_agent")
            fallback_res = await chat_agent.execute(state)
            if fallback_res.get("messages"):
                state["messages"].extend(fallback_res["messages"])

        return state

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
