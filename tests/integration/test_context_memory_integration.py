import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage

from app.AI_agents.orchestrator.agent_orchestrator import AgentOrchestrator
from app.AI_agents.memory.long_term_memory import LongTermMemoryStore, FactExtractor, FactCategory
from app.AI_agents.memory.memory_manager import MemoryManager
from app.AI_agents.context.context_builder import ContextBuilder
from app.AI_agents.context.context_types import ContextSource, ContextBundle


def test_end_to_end_escalation_flow_and_context_reuse():
    """
    End-to-End Integration Test:
    Verify full escalation flow from Tier 1 ChatAgent ➔ EscalationPolicy ➔ Tier 2 HealthAgent:
    - Tier 1 LLM answer generation is SKIPPED (Phase 2 fix)
    - Tier 1 RAG context is REUSED by Tier 2 (Phase 1 fix)
    - Output response comes from Tier 2 Specialist
    """
    async def _run():
        orchestrator = AgentOrchestrator()
        user_msg = "Bé 6 tháng bị sốt 38.5 độ từ sáng qua, có nên cho uống Hapacol 150mg không?"
        thread_id = "integration_thread_escalation"
        user_id = "integration_user_01"
        baby_id = "integration_baby_01"

        mock_checkpoint = MagicMock()
        mock_checkpoint.checkpoint = {"channel_values": {"messages": []}}

        with patch.object(orchestrator.checkpointer, "aget_tuple", AsyncMock(return_value=mock_checkpoint)), \
             patch("app.AI_agents.workflows.chat_graph.ChatAgentContract.generate_native_answer", AsyncMock()) as mock_tier1_gen, \
             patch("app.AI_agents.knowledge.retriever.MedicalRetriever.retrieve_context_with_plan", AsyncMock(return_value="Tài liệu WHO: Hapacol 150mg dùng cho bé 6 tháng sốt 38.5C.")) as mock_rag_search, \
             patch("app.AI_agents.workflows.health_graph.AIReasoner") as mock_reasoner_cls:

            mock_reasoner = MagicMock()
            mock_reasoner.areason_with_history = AsyncMock(return_value="Theo bác sĩ nhi khoa, bé 6 tháng sốt 38.5C dùng Hapacol 150mg đúng liều lượng.")
            mock_reasoner_cls.return_value = mock_reasoner

            res = await orchestrator.run_agent(
                message=user_msg,
                thread_id=thread_id,
                baby_id=baby_id,
                user_id=user_id
            )

            assert res is not None
            # 1. Tier 1 answer generation call MUST NOT be called on escalation
            mock_tier1_gen.assert_not_called()
            # 2. MedicalRetriever search called ONCE in Tier 1 and REUSED by Tier 2 (0 duplicate calls)
            mock_rag_search.assert_called_once()
            # 3. Response comes from HealthAgent
            assert "Hapacol 150mg" in res["messages"][-1].content

    asyncio.run(_run())


def test_end_to_end_cross_thread_long_term_memory():
    """
    End-to-End Integration Test:
    Verify cross-thread memory persistence:
    - Thread A: User states allergy fact ("Bé bị dị ứng hải sản")
    - Thread B (different thread_id, same user/baby): Querying nutrition automatically includes allergy fact
    """
    async def _run():
        user_id = "user_integration_cross"
        baby_id = "baby_integration_cross"

        memory_store = LongTermMemoryStore()
        extractor = FactExtractor(memory_store)

        # Thread 1: User mentions allergy
        msg_thread_1 = "Bé nhà mình bị dị ứng hải sản mẫn cảm."
        extracted = extractor.extract_and_store_facts(user_id, baby_id, msg_thread_1)
        assert len(extracted) > 0
        assert extracted[0].category == FactCategory.ALLERGY

        # Thread 2: Different conversation thread asking a nutrition question
        msg_thread_2 = "Hôm nay mình định làm súp tôm cho bé ăn dặm."
        long_term_facts = memory_store.format_facts_for_context(user_id, baby_id)

        bundle = ContextBuilder.build_chat_context(
            system_template="Trợ lý nhi khoa cho {baby_name}",
            baby_profile_data={"baby_name": "Bo", "baby_gender": "Nữ", "baby_age": "6", "baby_birth_date": "", "growth_info": ""},
            rag_context="",
            messages=[HumanMessage(content=msg_thread_2)],
            long_term_facts=long_term_facts
        )

        assert ContextSource.LONG_TERM_MEMORY in bundle.sources_included
        assert "DỮ LIỆU BỀN VỮNG VỀ BÉ (LONG-TERM FACTS)" in bundle.system_instruction
        assert "hải sản" in bundle.system_instruction.lower()

    asyncio.run(_run())


def test_end_to_end_conversation_summary_buffer_flow():
    """
    End-to-End Integration Test:
    Verify that when old conversation turns exceed budget, dropped messages trigger summary creation
    and inject conversation summary into prompt.
    """
    async def _run():
        memory_mgr = MemoryManager()

        old_dropped_msgs = [
            HumanMessage(content="Bé bị sốt từ chiều qua"),
            AIMessage(content="Bác sĩ khuyên chườm ấm và cho uống nhiều nước"),
            HumanMessage(content="Bé đã đỡ sốt chưa? Mẹ cần theo dõi gì nữa?"),
            AIMessage(content="Cần đo nhiệt độ mỗi 4 giờ.")
        ]

        with patch("app.AI_agents.core.reasoner.AIReasoner") as mock_reasoner_cls:
            mock_reasoner = MagicMock()
            mock_reasoner.areason_with_history = AsyncMock(return_value="Tóm tắt: Bé bị sốt từ chiều qua, đã được hướng dẫn chườm ấm và đo nhiệt độ 4h/lần.")
            mock_reasoner_cls.return_value = mock_reasoner

            summary = await memory_mgr.summarize_old_messages(old_dropped_msgs)
            assert "Bé bị sốt" in summary

            bundle = ContextBuilder.build_chat_context(
                system_template="System prompt",
                baby_profile_data={"baby_name": "Leo", "baby_gender": "Nam", "baby_age": "6", "baby_birth_date": "", "growth_info": ""},
                rag_context="",
                messages=[HumanMessage(content="Hôm nay bé tỉnh táo rồi.")],
                conversation_summary=summary
            )

            assert ContextSource.CONVERSATION_SUMMARY in bundle.sources_included
            assert "TÓM TẮT DIỄN BIẾN HỘI THOẠI TRƯỚC ĐÓ:" in bundle.system_instruction
            assert summary in bundle.system_instruction

    asyncio.run(_run())
