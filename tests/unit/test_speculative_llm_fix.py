import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator
from app.AI_agents.workflows.chat_graph import ChatAgentContract
from app.AI_agents.core.contract import Tier1Result


def test_speculative_llm_call_skipped_on_escalation():
    """Verify that Tier 1 LLM answer generation is SKIPPED when escalation occurs."""
    async def _run():
        orchestrator = AgentOrchestrator()

        escalating_query = "Bé bị sốt 38.5 độ từ sáng qua, uống Hapacol 150mg được không?"
        thread_id = "test_thread_speculative"
        baby_id = "test_baby_id"
        user_id = "test_user_id"

        mock_checkpoint = MagicMock()
        mock_checkpoint.checkpoint = {"channel_values": {"messages": []}}

        with patch.object(orchestrator.checkpointer, "aget_tuple", AsyncMock(return_value=mock_checkpoint)), \
             patch("app.AI_agents.workflows.chat_graph.ChatAgentContract.generate_native_answer", AsyncMock()) as mock_tier1_llm_gen, \
             patch("app.AI_agents.knowledge.retriever.MedicalRetriever.retrieve_context_with_plan", AsyncMock(return_value="Tài liệu WHO RAG.")), \
             patch("app.AI_agents.workflows.health_graph.HealthAgentContract.execute_with_context", AsyncMock(return_value={"messages": [AIMessage(content="Tier 2 Specialist Answer")], "tool_steps": []})):

            res = await orchestrator.run_agent(
                message=escalating_query,
                thread_id=thread_id,
                baby_id=baby_id,
                user_id=user_id
            )

            assert res is not None
            # Crucial assertion: Tier 1 LLM answer generation MUST NOT be called when escalating!
            mock_tier1_llm_gen.assert_not_called()
            # Verify response comes from Tier 2
            assert res["messages"][-1].content == "Tier 2 Specialist Answer"

    asyncio.run(_run())


def test_tier1_native_answer_generated_when_no_escalation():
    """Verify that Tier 1 LLM answer generation IS called when no escalation occurs."""
    async def _run():
        orchestrator = AgentOrchestrator()

        native_query = "Bé mấy tháng tuổi thì bắt đầu tập lẫy ạ?"
        thread_id = "test_thread_native"
        baby_id = "test_baby_id"
        user_id = "test_user_id"

        mock_checkpoint = MagicMock()
        mock_checkpoint.checkpoint = {"channel_values": {"messages": []}}

        with patch.object(orchestrator.checkpointer, "aget_tuple", AsyncMock(return_value=mock_checkpoint)), \
             patch("app.AI_agents.workflows.chat_graph.ChatAgentContract.generate_native_answer", AsyncMock(return_value="Bé thường tập lẫy từ 3-4 tháng tuổi ạ.")) as mock_tier1_llm_gen:

            res = await orchestrator.run_agent(
                message=native_query,
                thread_id=thread_id,
                baby_id=baby_id,
                user_id=user_id
            )

            assert res is not None
            mock_tier1_llm_gen.assert_called_once()
            assert res["messages"][-1].content == "Bé thường tập lẫy từ 3-4 tháng tuổi ạ."

    asyncio.run(_run())
