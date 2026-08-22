import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.AI_agents.workflows.health_graph import HealthAgentContract
from app.AI_agents.workflows.nutrition_graph import NutritionAgentContract


def test_health_agent_context_reuse():
    """Verify HealthAgentContract reuses rag_context from Tier 1 without calling MedicalRetriever."""
    async def _run():
        mock_rag_context = "RAG WHO Guideline for fever care: Give Paracetamol 10-15mg/kg."
        tier1_context = {
            "user_query": "Bé bị sốt 38.5 độ uống thuốc gì?",
            "rag_context": mock_rag_context,
            "tool_steps": []
        }
        state = {
            "messages": [HumanMessage(content="Bé bị sốt 38.5 độ uống thuốc gì?")],
            "baby_id": "test_baby_id",
            "current_user_id": "test_user_id",
            "tool_steps": []
        }

        with patch("app.AI_agents.workflows.health_graph.MedicalRetriever") as mock_retriever_cls, \
             patch("app.AI_agents.workflows.health_graph.AIReasoner") as mock_reasoner_cls, \
             patch("app.AI_agents.workflows.health_graph.HealthRecordsTool") as mock_tool_cls:
            
            mock_reasoner = MagicMock()
            mock_reasoner.areason_with_history = AsyncMock(return_value="Nên cho bé uống Hapacol 150mg theo chỉ định.")
            mock_reasoner_cls.return_value = mock_reasoner

            health_contract = HealthAgentContract()

            res = await health_contract.execute_with_context(
                query="Bé bị sốt 38.5 độ uống thuốc gì?",
                state=state,
                tier1_context=tier1_context,
                retrieved_docs=[]
            )

            assert res is not None
            assert state.get("rag_context_reused") is True
            assert state.get("rag_context") == mock_rag_context
            mock_retriever_cls.return_value.retrieve_context.assert_not_called()

    asyncio.run(_run())


def test_nutrition_agent_context_reuse():
    """Verify NutritionAgentContract reuses rag_context from Tier 1 without calling MedicalRetriever."""
    async def _run():
        mock_rag_context = "WHO Feeding Guide: Solid food starting at 6 months."
        tier1_context = {
            "user_query": "Bé 6 tháng ăn dặm như thế nào?",
            "rag_context": mock_rag_context,
            "tool_steps": []
        }
        state = {
            "messages": [HumanMessage(content="Bé 6 tháng ăn dặm như thế nào?")],
            "baby_id": "test_baby_id",
            "current_user_id": "test_user_id",
            "tool_steps": []
        }

        with patch("app.AI_agents.workflows.nutrition_graph.MedicalRetriever") as mock_retriever_cls, \
             patch("app.AI_agents.workflows.nutrition_graph.AIReasoner") as mock_reasoner_cls, \
             patch("app.AI_agents.workflows.nutrition_graph.NutritionTrackingTool") as mock_nutr_tool, \
             patch("app.AI_agents.workflows.nutrition_graph.GrowthTrackingTool") as mock_growth_tool:
            
            mock_reasoner = MagicMock()
            mock_reasoner.areason_with_history = AsyncMock(return_value="Nên bắt đầu cho bé ăn cháo rây 1:10.")
            mock_reasoner_cls.return_value = mock_reasoner

            nutrition_contract = NutritionAgentContract()

            res = await nutrition_contract.execute_with_context(
                query="Bé 6 tháng ăn dặm như thế nào?",
                state=state,
                tier1_context=tier1_context,
                retrieved_docs=[]
            )

            assert res is not None
            assert state.get("rag_context_reused") is True
            assert state.get("rag_context") == mock_rag_context
            mock_retriever_cls.return_value.retrieve_context_with_plan.assert_not_called()

    asyncio.run(_run())
