import pytest
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from app.AI_agents.memory.memory_manager import MemoryManager


def test_token_aware_memory_preserves_short_messages():
    memory_mgr = MemoryManager()
    # Create 20 short messages
    messages = [SystemMessage(content="System instruction")]
    for i in range(20):
        messages.append(HumanMessage(content=f"Câu hỏi ngắn số {i}"))
        messages.append(AIMessage(content=f"Trả lời ngắn số {i}"))

    # With a budget of 2000 tokens, all 40 short messages should easily fit
    selected = memory_mgr.select_messages_by_token_budget(messages, max_history_tokens=2000)

    assert isinstance(selected[0], SystemMessage)
    # Total selected should be > 15 messages (verifying we are no longer limited to hardcoded 15)
    assert len(selected) > 15
    assert selected[-1].content == "Trả lời ngắn số 19"


def test_token_aware_memory_truncates_large_messages():
    memory_mgr = MemoryManager()
    messages = [SystemMessage(content="System instruction")]
    
    # Add large messages (500 tokens each)
    for i in range(10):
        messages.append(HumanMessage(content=f"Tin nhắn dài số {i}: " + ("thông tin y tế " * 250)))

    # With a budget of 600 tokens, only the last ~1-2 messages should fit
    selected = memory_mgr.select_messages_by_token_budget(messages, max_history_tokens=600)

    assert isinstance(selected[0], SystemMessage)
    assert len(selected) < len(messages)
    # The latest message must always be preserved
    assert selected[-1].content == messages[-1].content
