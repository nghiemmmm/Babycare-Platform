import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.AI_agents.context.token_budget import TokenBudget
from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator


def test_token_budget_cost_calculation():
    # Model Pricing test for gemini-2.0-flash ($0.10 input / 1M, $0.40 output / 1M)
    cost = TokenBudget.calculate_cost_usd("gemini-2.0-flash", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == 0.50

    # Model Pricing test for gemini-1.5-pro ($1.25 input / 1M, $5.00 output / 1M)
    cost_pro = TokenBudget.calculate_cost_usd("gemini-1.5-pro", input_tokens=100_000, output_tokens=10_000)
    assert round(cost_pro, 4) == round(0.125 + 0.05, 4)


def test_orchestrator_attaches_financial_observability():
    async def _run():
        orchestrator = AgentOrchestrator()

        mock_checkpoint = MagicMock()
        mock_checkpoint.checkpoint = {"channel_values": {"messages": []}}

        with patch.object(orchestrator.checkpointer, "aget_tuple", AsyncMock(return_value=mock_checkpoint)), \
             patch("app.AI_agents.workflows.chat_graph.ChatGraph.generate_answer_from_prep", AsyncMock(return_value="Bé 6 tháng tuổi bắt đầu tập lẫy ạ.")):

            state = await orchestrator.run_agent(
                message="Bé mấy tháng tuổi bắt đầu tập lẫy?",
                thread_id="test_financial_thread",
                baby_id="test_baby",
                user_id="test_user"
            )

            assert state is not None
            assert "financial_observability" in state
            obs = state["financial_observability"]
            assert "latency_ms" in obs
            assert "total_tokens" in obs
            assert "estimated_cost_usd" in obs
            assert obs["latency_ms"] >= 0
            assert obs["estimated_cost_usd"] >= 0.0

    asyncio.run(_run())
