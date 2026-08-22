import pytest
from app.AI_agents.core.cry_policy_engine import CryPolicyEngine, ACTION_WHITELIST
from app.modules.cry.schemas import (
    AdjustedEvidence,
    CryContextBundle,
    HealthContext
)


def test_safety_gate_emergency_trigger():
    """
    TEST 1: Khi bé có cờ đỏ y tế (sốt cao >= 38.5, co giật, khó thở),
    Safety Gate phải lập tức kích hoạt EMERGENCY, Action SEEK_EMERGENCY_CARE và KHÔNG phát nhạc ru.
    """
    adjusted = AdjustedEvidence(
        primary_cause="pain",
        adjusted_confidence=0.85,
        adjusted_scores={"pain": 0.85, "discomfort": 0.15},
        applied_rules=["HEALTH_FEVER_OR_SYMPTOM_BOOSTS_PAIN"]
    )
    context = CryContextBundle(
        health=HealthContext(
            available=True,
            temperature=39.2,
            has_fever=True,
            is_high_risk=True,
            symptoms=["Sốt cao", "Co giật"]
        )
    )

    decision = CryPolicyEngine.evaluate(adjusted, context)

    assert decision.risk_level == "EMERGENCY"
    assert "SEEK_EMERGENCY_CARE" in decision.action_plan
    assert decision.soothing_sound is None # Cấp cứu: Không bật nhạc ru gây trì hoãn
    assert "SAFETY_GATE_EMERGENCY_TRIGGERED" in decision.applied_policies
    assert decision.safety_message is not None


def test_safety_gate_fever_monitoring():
    """
    TEST 2: Sốt 38.2 độ (chưa đạt high risk) -> Cấp độ HIGH, yêu cầu CHECK_TEMPERATURE và theo dõi.
    """
    adjusted = AdjustedEvidence(
        primary_cause="pain",
        adjusted_confidence=0.70,
        adjusted_scores={"pain": 0.70, "discomfort": 0.30}
    )
    context = CryContextBundle(
        health=HealthContext(
            available=True,
            temperature=38.2,
            has_fever=True,
            is_high_risk=False
        )
    )

    decision = CryPolicyEngine.evaluate(adjusted, context)

    assert decision.risk_level == "HIGH"
    assert "CHECK_TEMPERATURE" in decision.action_plan
    assert "CONTACT_DOCTOR" in decision.action_plan


def test_policy_burp_action_plan():
    """
    TEST 3: Trẻ khóc do cần ợ hơi (burp) -> Action: BURP + SOOTHE, Sound: lullaby.
    """
    adjusted = AdjustedEvidence(
        primary_cause="burp",
        adjusted_confidence=0.82,
        adjusted_scores={"burp": 0.82, "discomfort": 0.18}
    )
    context = CryContextBundle()

    decision = CryPolicyEngine.evaluate(adjusted, context)

    assert decision.risk_level == "LOW"
    assert "BURP" in decision.action_plan
    assert "SOOTHE" in decision.action_plan
    assert all(act in ACTION_WHITELIST for act in decision.action_plan)
    assert decision.soothing_sound is not None


def test_policy_action_whitelist_enforcement():
    """
    TEST 4: Khẳng định 100% action_plan trong mọi Decision đều nằm trong Whitelist y khoa.
    """
    for cause in ["hungry", "tired", "pain", "burp", "discomfort", "scared", "lonely", "unknown"]:
        adj = AdjustedEvidence(
            primary_cause=cause,
            adjusted_confidence=0.80,
            adjusted_scores={cause: 0.80}
        )
        dec = CryPolicyEngine.evaluate(adj, CryContextBundle())
        for act in dec.action_plan:
            assert act in ACTION_WHITELIST, f"Action {act} không nằm trong whitelist!"
