import pytest
from langchain_core.messages import HumanMessage, AIMessage

from app.AI_agents.context.context_types import ContextSource, ContextItem, ContextBundle
from app.AI_agents.context.token_budget import TokenBudget
from app.AI_agents.context.context_builder import ContextBuilder


def test_token_budget_estimation():
    text = "Chào mẹ! Em là trợ lý BabyCare AI."
    estimated = TokenBudget.estimate_tokens(text)
    assert estimated > 0
    assert isinstance(estimated, int)


def test_token_budget_allocation_and_rag_truncation():
    large_rag = "từ " * 1000  # 1000 words -> approx 1300 tokens
    item_rag = ContextItem(
        source=ContextSource.RAG_DOCS,
        content=large_rag,
        priority=70,
        token_count=1300
    )
    allocated = TokenBudget.allocate_items([item_rag], max_budget=4000)
    assert len(allocated) == 1
    assert allocated[0].token_count <= TokenBudget.RAG_MAX_TOKENS


def test_context_builder_chat_bundle():
    sys_template = "Bạn là trợ lý BabyCare AI hỗ trợ cho bé {baby_name} ({baby_age} tháng)."
    baby_data = {
        "baby_name": "Leo",
        "baby_gender": "Nam",
        "baby_age": "6",
        "baby_birth_date": "2023-04-20",
        "growth_info": "Chiều cao 66cm, Cân nặng 7.2kg"
    }
    rag_text = "Tài liệu WHO hướng dẫn ăn dặm từ 6 tháng."
    messages = [HumanMessage(content="Bé 6 tháng ăn dặm được chưa?")]

    bundle = ContextBuilder.build_chat_context(
        system_template=sys_template,
        baby_profile_data=baby_data,
        rag_context=rag_text,
        messages=messages
    )

    assert isinstance(bundle, ContextBundle)
    assert "Leo" in bundle.system_instruction
    assert "WHO" in bundle.system_instruction
    assert len(bundle.messages) == 1
    assert bundle.total_tokens > 0
    assert ContextSource.SYSTEM_INSTRUCTION in bundle.sources_included
    assert ContextSource.RAG_DOCS in bundle.sources_included
    assert ContextSource.RECENT_MESSAGES in bundle.sources_included
