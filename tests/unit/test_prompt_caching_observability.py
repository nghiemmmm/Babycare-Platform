import pytest
from langchain_core.messages import HumanMessage
from app.AI_agents.context.context_builder import ContextBuilder
from app.AI_agents.core.constant import CHAT_SYSTEM_PROMPT_TEMPLATE, HEALTH_SYSTEM_PROMPT
from app.AI_agents.core.reasoner import AIReasoner


# =====================================================================
# LEVEL 1 — UNIT TESTS
# =====================================================================

def test_static_prefix_always_before_dynamic_content():
    """1. Static prefix (Persona, Guardrails, Rules) luôn đứng trước dynamic content."""
    baby_data = {
        "baby_name": "Leo",
        "baby_gender": "Nam",
        "baby_age": "6",
        "baby_birth_date": "2023-04-20",
        "growth_info": "66cm, 7.2kg"
    }
    rag_context = "WHO Guidelines on weaning at 6 months."
    long_term_facts = "- Dị ứng: Đậu nành"
    summary = "Bé đã tiêm phòng mũi 6in1 tháng trước."

    bundle = ContextBuilder.build_chat_context(
        system_template=CHAT_SYSTEM_PROMPT_TEMPLATE,
        baby_profile_data=baby_data,
        rag_context=rag_context,
        messages=[HumanMessage(content="Bé ăn dặm mấy bữa?")],
        conversation_summary=summary,
        long_term_facts=long_term_facts
    )

    sys_text = bundle.system_instruction

    # Vị trí các section
    pos_identity = sys_text.find("# IDENTITY & PERSONA")
    pos_guardrails = sys_text.find("# GUARDRAILS & VĂN PHONG NHI KHOA")
    pos_rules = sys_text.find("# REACT REASONING & AUTO-STOP RULES")
    pos_profile = sys_text.find("# CONTEXT HỒ SƠ BÉ")
    pos_long_term = sys_text.find("# DỮ LIỆU BỀN VỮNG VỀ BÉ")
    pos_summary = sys_text.find("# TÓM TẮT DIỄN BIẾN HỘI THOẠI TRƯỚC ĐÓ")
    pos_rag = sys_text.find("# TÀI LIỆU THAM CHIẾU RAG WHO")

    # Kiểm tra thứ tự nghiêm ngặt (Static -> Semi-Static -> Dynamic)
    assert pos_identity < pos_guardrails < pos_rules < pos_profile
    assert pos_profile < pos_long_term < pos_summary < pos_rag


def test_dynamic_rag_never_before_static_prefix():
    """2. Dynamic RAG không được chèn trước static prefix."""
    bundle = ContextBuilder.build_chat_context(
        system_template=CHAT_SYSTEM_PROMPT_TEMPLATE,
        baby_profile_data={"baby_name": "Bo"},
        rag_context="RAG WHO Nutrition Data...",
        messages=[HumanMessage(content="Bé uống sữa gì?")]
    )

    sys_text = bundle.system_instruction
    pos_identity = sys_text.find("# IDENTITY & PERSONA")
    pos_rag = sys_text.find("# TÀI LIỆU THAM CHIẾU RAG WHO")

    assert pos_rag > pos_identity
    assert pos_rag != -1


def test_cached_tokens_parsed_from_gemini_metadata():
    """3. cached_tokens được parse đúng từ Gemini metadata (cached_content_token_count)."""
    gemini_usage = {
        "input_tokens": 2500,
        "output_tokens": 150,
        "total_tokens": 2650,
        "cached_content_token_count": 1800
    }

    parsed = AIReasoner.parse_usage_metadata(gemini_usage)

    assert parsed["prompt_tokens"] == 2500
    assert parsed["completion_tokens"] == 150
    assert parsed["cached_tokens"] == 1800
    assert parsed["cached_token_ratio_pct"] == 72.0


def test_cached_tokens_parsed_from_openrouter_metadata():
    """4. cached_tokens được parse đúng từ OpenRouter/OpenAI metadata (prompt_tokens_details.cached_tokens)."""
    openrouter_usage = {
        "prompt_tokens": 2000,
        "completion_tokens": 200,
        "total_tokens": 2200,
        "prompt_tokens_details": {
            "cached_tokens": 1500
        }
    }

    parsed = AIReasoner.parse_usage_metadata(openrouter_usage)

    assert parsed["prompt_tokens"] == 2000
    assert parsed["completion_tokens"] == 200
    assert parsed["cached_tokens"] == 1500
    assert parsed["cached_token_ratio_pct"] == 75.0


def test_cached_token_ratio_calculation():
    """5. cached_token_ratio được tính đúng theo tỷ lệ %."""
    # 50% hit
    usage_half = {"input_tokens": 1000, "cached_content_token_count": 500}
    assert AIReasoner.parse_usage_metadata(usage_half)["cached_token_ratio_pct"] == 50.0

    # 0% hit
    usage_zero = {"input_tokens": 1000, "cached_content_token_count": 0}
    assert AIReasoner.parse_usage_metadata(usage_zero)["cached_token_ratio_pct"] == 0.0

    # 100% hit
    usage_full = {"input_tokens": 1000, "cached_content_token_count": 1000}
    assert AIReasoner.parse_usage_metadata(usage_full)["cached_token_ratio_pct"] == 100.0


def test_cache_metrics_logged_in_reasoner():
    """6. Cache metrics được ghi nhận và trả về từ _log_reasoning."""
    reasoner = AIReasoner(model_name="gemini-3.5-flash-lite")
    usage = {
        "input_tokens": 3000,
        "output_tokens": 300,
        "cached_content_token_count": 2100
    }

    logged_stats = reasoner._log_reasoning(
        system_instruction="Static Sys Instruction",
        prompt="User prompt",
        response_text="AI response",
        elapsed=0.45,
        usage_metadata=usage
    )

    assert logged_stats["cached_tokens"] == 2100
    assert logged_stats["cached_token_ratio_pct"] == 70.0
    assert logged_stats["prompt_tokens"] == 3000


# =====================================================================
# LEVEL 2 — PROMPT STABILITY TEST
# =====================================================================

def test_prompt_stability_common_prefix():
    """
    Generate prompt cho Request A và Request B (khác Query & RAG Context).
    Verify common_prefix(A, B) giữ nguyên toàn bộ Static Prefix & Hồ sơ.
    """
    baby_data = {
        "baby_name": "Leo",
        "baby_gender": "Nam",
        "baby_age": "6",
        "baby_birth_date": "2023-04-20",
        "growth_info": "66cm, 7.2kg"
    }

    # Request A
    bundle_a = ContextBuilder.build_chat_context(
        system_template=CHAT_SYSTEM_PROMPT_TEMPLATE,
        baby_profile_data=baby_data,
        rag_context="--- TÀI LIỆU ĂN DẶM 6 THÁNG: Bắt đầu từ bột ngọt loãng, 1 bữa/ngày. ---",
        messages=[HumanMessage(content="Bé 6 tháng ăn dặm mấy bữa 1 ngày?")]
    )

    # Request B
    bundle_b = ContextBuilder.build_chat_context(
        system_template=CHAT_SYSTEM_PROMPT_TEMPLATE,
        baby_profile_data=baby_data,
        rag_context="--- TÀI LIỆU TIÊM CHỦNG 6 THÁNG: Mũi nhắc cúm mùa và phế cầu. ---",
        messages=[HumanMessage(content="Lịch tiêm phòng tháng thứ 6 của bé?")]
    )

    prompt_a = bundle_a.system_instruction
    prompt_b = bundle_b.system_instruction

    # Tìm common prefix dài nhất
    def get_common_prefix(s1: str, s2: str) -> str:
        idx = 0
        min_len = min(len(s1), len(s2))
        while idx < min_len and s1[idx] == s2[idx]:
            idx += 1
        return s1[:idx]

    common = get_common_prefix(prompt_a, prompt_b)

    # Common Prefix phải chứa toàn bộ Static Rules & Baby Profile
    assert "# IDENTITY & PERSONA" in common
    assert "# GUARDRAILS & VĂN PHONG NHI KHOA" in common
    assert "# REACT REASONING & AUTO-STOP RULES" in common
    assert "# CONTEXT HỒ SƠ BÉ" in common
    assert "- Tên bé: Leo" in common
    assert "- Số tháng tuổi: 6 tháng" in common

    # Phần RAG động của Request A và B nằm ngoài Common Prefix
    assert "TÀI LIỆU ĂN DẶM" not in common
    assert "TÀI LIỆU TIÊM CHỦNG" not in common
    assert len(common) > 400  # Prefix chung đủ lớn để kích hoạt Prompt Caching
