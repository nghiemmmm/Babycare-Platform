import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.AI_agents.memory.memory_manager import MemoryManager
from app.AI_agents.context.context_builder import ContextBuilder
from app.AI_agents.context.context_types import ContextSource, ContextBundle


def test_summarize_old_messages_triggers_on_threshold():
    async def _run():
        memory_mgr = MemoryManager()

        # Less than 3 dropped messages -> returns existing summary without calling LLM
        dropped_few = [HumanMessage(content="Tin nhắn 1"), AIMessage(content="Trả lời 1")]
        summary_few = await memory_mgr.summarize_old_messages(dropped_few, existing_summary="Summary cũ")
        assert summary_few == "Summary cũ"

        # 3 or more dropped messages -> calls AIReasoner
        dropped_many = [
            HumanMessage(content="Bé bị sốt 38.5 độ"),
            AIMessage(content="Mẹ nên hạ sốt bằng khăn ấm và Hapacol."),
            HumanMessage(content="Cảm ơn bác sĩ.")
        ]

        with patch("app.AI_agents.core.reasoner.AIReasoner") as mock_reasoner_cls:
            mock_reasoner = MagicMock()
            mock_reasoner.areason_with_history = AsyncMock(return_value="Bé bị sốt 38.5 độ, mẹ đã nhận hướng dẫn dùng Hapacol.")
            mock_reasoner_cls.return_value = mock_reasoner

            new_summary = await memory_mgr.summarize_old_messages(dropped_many, existing_summary="Hồ sơ sức khỏe ban đầu.")
            assert new_summary == "Bé bị sốt 38.5 độ, mẹ đã nhận hướng dẫn dùng Hapacol."
            mock_reasoner.areason_with_history.assert_called_once()

    asyncio.run(_run())


def test_context_builder_injects_conversation_summary():
    sys_template = "Bạn là trợ lý BabyCare AI hỗ trợ cho bé {baby_name} ({baby_age} tháng)."
    baby_data = {"baby_name": "Bo", "baby_gender": "Nữ", "baby_age": "3", "baby_birth_date": "2023-11-15", "growth_info": ""}
    summary_text = "Mẹ lo lắng bé quấy khóc ban đêm."

    bundle = ContextBuilder.build_chat_context(
        system_template=sys_template,
        baby_profile_data=baby_data,
        rag_context="",
        messages=[HumanMessage(content="Bé ngủ được chưa mẹ?")],
        conversation_summary=summary_text
    )

    assert isinstance(bundle, ContextBundle)
    assert ContextSource.CONVERSATION_SUMMARY in bundle.sources_included
    assert "TÓM TẮT DIỄN BIẾN HỘI THOẠI TRƯỚC ĐÓ:" in bundle.system_instruction
    assert "Mẹ lo lắng bé quấy khóc ban đêm." in bundle.system_instruction
