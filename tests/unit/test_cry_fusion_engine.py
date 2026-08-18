import pytest
from app.AI_agents.core.cry_fusion_engine import ExplicitContextFusion
from app.modules.cry.schemas import (
    AudioEvidence,
    CryContextBundle,
    FeedingContext,
    SleepContext,
    HealthContext,
    MedicationContext
)


def test_fusion_rule_recent_feed_contradicts_hunger():
    """
    TEST 1: AST hungry=0.90, vừa ăn 10 phút trước.
    Phải phát hiện mâu thuẫn, giảm hungry, tăng burp và discomfort.
    """
    audio = AudioEvidence(
        top_label="hungry",
        confidence=0.90,
        reason_scores={"hungry": 0.90, "pain": 0.05, "tired": 0.05}
    )
    context = CryContextBundle(
        feeding=FeedingContext(
            available=True,
            food_name="Sữa công thức",
            amount_g=150.0,
            minutes_since_feed=10 # 10 phút
        )
    )

    adjusted = ExplicitContextFusion.fuse(audio, context)

    assert "RECENT_FEED_CONTRADICTS_HUNGER" in adjusted.applied_rules
    assert adjusted.contradiction_score >= 0.80
    assert adjusted.primary_cause in ["burp", "discomfort"]
    assert adjusted.adjusted_scores["hungry"] < 0.40
    assert adjusted.adjusted_scores["burp"] > adjusted.adjusted_scores["hungry"]


def test_fusion_rule_long_fasting_confirms_hunger():
    """
    TEST 2: AST hungry=0.70, đã 4 tiếng chưa ăn (240 phút).
    Phải củng cố và tăng điểm hungry.
    """
    audio = AudioEvidence(
        top_label="hungry",
        confidence=0.70,
        reason_scores={"hungry": 0.70, "tired": 0.20, "pain": 0.10}
    )
    context = CryContextBundle(
        feeding=FeedingContext(
            available=True,
            minutes_since_feed=240 # 4 tiếng
        )
    )

    adjusted = ExplicitContextFusion.fuse(audio, context)

    assert "LONG_FASTING_CONFIRMS_HUNGER" in adjusted.applied_rules
    assert adjusted.primary_cause == "hungry"
    assert adjusted.adjusted_confidence >= 0.70


def test_fusion_rule_long_wake_window_boosts_tired():
    """
    TEST 3: Bé đã thức 150 phút (2.5 tiếng) -> củng cố tiếng khóc gắt ngủ (tired).
    """
    audio = AudioEvidence(
        top_label="tired",
        confidence=0.50,
        reason_scores={"tired": 0.50, "hungry": 0.30, "discomfort": 0.20}
    )
    context = CryContextBundle(
        sleep=SleepContext(
            available=True,
            wake_window_minutes=150
        )
    )

    adjusted = ExplicitContextFusion.fuse(audio, context)

    assert "LONG_WAKE_WINDOW_BOOSTS_TIRED" in adjusted.applied_rules
    assert adjusted.primary_cause == "tired"
    assert adjusted.adjusted_scores["tired"] > 0.50


def test_fusion_rule_fever_boosts_pain():
    """
    TEST 4: AST pain=0.60, bé đang sốt 38.8 độ -> tăng điểm pain.
    """
    audio = AudioEvidence(
        top_label="pain",
        confidence=0.60,
        reason_scores={"pain": 0.60, "discomfort": 0.30, "tired": 0.10}
    )
    context = CryContextBundle(
        health=HealthContext(
            available=True,
            temperature=38.8,
            has_fever=True,
            is_high_risk=True
        )
    )

    adjusted = ExplicitContextFusion.fuse(audio, context)

    assert "HEALTH_FEVER_OR_SYMPTOM_BOOSTS_PAIN" in adjusted.applied_rules
    assert adjusted.primary_cause == "pain"
    assert adjusted.adjusted_scores["pain"] > 0.65


def test_entropy_uncertainty_calculation():
    """
    TEST 5: Đo lường độ bất định phân phối xác suất.
    - Phân phối phân tán (0.25, 0.25, 0.25, 0.25) -> entropy cao ~1.0
    - Phân phối tập trung (0.95, 0.05) -> entropy thấp ~0.0
    """
    diffuse_scores = {"hungry": 0.25, "pain": 0.25, "tired": 0.25, "burp": 0.25}
    diffuse_entropy = ExplicitContextFusion.calculate_entropy_uncertainty(diffuse_scores)
    assert diffuse_entropy >= 0.90

    certain_scores = {"hungry": 0.98, "pain": 0.01, "tired": 0.01}
    certain_entropy = ExplicitContextFusion.calculate_entropy_uncertainty(certain_scores)
    assert certain_entropy <= 0.25
