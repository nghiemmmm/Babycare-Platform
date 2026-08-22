import pytest
from app.AI_agents.knowledge.rag_trigger import RAGTriggerEvaluator


def test_chitchat_bypasses_rag():
    greetings = ["Chào bạn", "hi", "cảm ơn bạn", "tạm biệt", "ok"]
    for g in greetings:
        should_trigger, reason = RAGTriggerEvaluator.should_trigger_rag(g)
        assert should_trigger is False
        assert reason == "chitchat_bypass"


def test_personal_db_queries_bypass_rag():
    queries = ["Bé nặng bao nhiêu kg?", "Bé được mấy tháng tuổi rồi?", "Bé cao bao nhiêu cm?"]
    for q in queries:
        should_trigger, reason = RAGTriggerEvaluator.should_trigger_rag(q)
        assert should_trigger is False
        assert reason == "personal_profile_bypass"


def test_knowledge_queries_trigger_rag():
    medical_queries = [
        "Bé bị sốt 38.5 độ uống thuốc Hapacol 150mg được không?",
        "Thực đơn ăn dặm chuẩn WHO cho bé 6 tháng",
        "Mốc phát triển tập lẫy của trẻ sơ sinh"
    ]
    for q in medical_queries:
        should_trigger, reason = RAGTriggerEvaluator.should_trigger_rag(q)
        assert should_trigger is True
        assert reason in ["medical_nutrition_guideline", "general_knowledge_query"]
