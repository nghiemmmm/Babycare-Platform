import pytest
from langchain_core.messages import HumanMessage

from app.AI_agents.memory.long_term_memory import LongTermMemoryStore, FactExtractor, FactCategory
from app.AI_agents.context.context_builder import ContextBuilder
from app.AI_agents.context.context_types import ContextSource, ContextBundle


def test_fact_extraction_and_cross_thread_retrieval():
    memory_store = LongTermMemoryStore()
    extractor = FactExtractor(memory_store)

    user_id = "user_test_cross_thread"
    baby_id = "baby_test_cross_thread"

    # Thread 1: User mentions an allergy
    user_msg_1 = "Bé nhà mình bị dị ứng đậu nành nặng lắm."
    extracted_1 = extractor.extract_and_store_facts(user_id, baby_id, user_msg_1)

    assert len(extracted_1) > 0
    assert extracted_1[0].category == FactCategory.ALLERGY
    assert "đậu nành" in extracted_1[0].fact.lower()

    # Thread 2: New thread for same user & baby -> retrieve facts
    facts_text = memory_store.format_facts_for_context(user_id, baby_id)
    assert "ALLERGY" in facts_text
    assert "đậu nành" in facts_text.lower()


def test_context_builder_injects_long_term_memory():
    sys_template = "Trợ lý BabyCare cho bé {baby_name}."
    baby_data = {"baby_name": "Leo", "baby_gender": "Nam", "baby_age": "6", "baby_birth_date": "", "growth_info": ""}
    long_term_text = "- [ALLERGY] Bé bị dị ứng đậu nành"

    bundle = ContextBuilder.build_chat_context(
        system_template=sys_template,
        baby_profile_data=baby_data,
        rag_context="",
        messages=[HumanMessage(content="Hôm nay bé ăn gì được?")],
        long_term_facts=long_term_text
    )

    assert isinstance(bundle, ContextBundle)
    assert ContextSource.LONG_TERM_MEMORY in bundle.sources_included
    assert "DỮ LIỆU BỀN VỮNG VỀ BÉ (LONG-TERM FACTS)" in bundle.system_instruction
    assert "dị ứng đậu nành" in bundle.system_instruction
