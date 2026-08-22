import pytest
from langchain_core.messages import HumanMessage

from app.AI_agents.context.context_builder import ContextBuilder
from app.AI_agents.context.context_types import ContextSource, ContextBundle


def test_context_bundle_to_dict_serialization():
    bundle = ContextBundle(
        system_instruction="System prompt test",
        messages=[HumanMessage(content="Test message")],
        rag_context="RAG WHO context",
        long_term_facts="- [ALLERGY] Soy allergy",
        conversation_summary="Previous conversation summary",
        total_tokens=250,
        token_breakdown={"system_instruction": 100, "rag_docs": 100, "recent_messages": 50},
        sources_included=[ContextSource.SYSTEM_INSTRUCTION, ContextSource.RAG_DOCS, ContextSource.RECENT_MESSAGES]
    )

    d = bundle.to_dict()
    assert d["system_instruction"] == "System prompt test"
    assert d["message_count"] == 1
    assert d["rag_context"] == "RAG WHO context"
    assert d["long_term_facts"] == "- [ALLERGY] Soy allergy"
    assert d["conversation_summary"] == "Previous conversation summary"
    assert d["total_tokens"] == 250
    assert "system_instruction" in d["token_breakdown"]
    assert "system_instruction" in d["sources_included"]


def test_standardized_context_bundles_across_builders():
    sys_template = "Prompt template {baby_name}"
    baby_data = {"baby_name": "Bo", "baby_gender": "Nữ", "baby_age": "3", "baby_birth_date": "", "growth_info": ""}

    chat_bundle = ContextBuilder.build_chat_context(
        system_template=sys_template,
        baby_profile_data=baby_data,
        rag_context="RAG text",
        messages=[HumanMessage(content="Hello")],
        conversation_summary="Summary text",
        long_term_facts="Fact text"
    )

    health_bundle = ContextBuilder.build_health_context(
        base_prompt="Health prompt",
        health_records_context="Health records",
        rag_context="RAG text",
        messages=[HumanMessage(content="Health question")],
        conversation_summary="Summary text",
        long_term_facts="Fact text"
    )

    logging_bundle = ContextBuilder.build_logging_context(
        extraction_prompt="Extraction prompt",
        messages=[HumanMessage(content="Bé vừa uống 150ml sữa")]
    )

    for bundle in [chat_bundle, health_bundle, logging_bundle]:
        assert isinstance(bundle, ContextBundle)
        assert hasattr(bundle, "system_instruction")
        assert hasattr(bundle, "messages")
        assert hasattr(bundle, "rag_context")
        assert hasattr(bundle, "long_term_facts")
        assert hasattr(bundle, "conversation_summary")
        assert hasattr(bundle, "total_tokens")
        assert hasattr(bundle, "token_breakdown")
        assert hasattr(bundle, "to_dict")

        d = bundle.to_dict()
        assert isinstance(d, dict)
        assert "total_tokens" in d
