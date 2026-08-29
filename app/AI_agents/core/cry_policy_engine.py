"""
Cry Safety Gate & Policy Engine
===============================
Chốt chặn an toàn y tế (Safety Gate) và Động cơ Quyết định Hành động (Policy Engine).
Chạy hoàn toàn TRƯỚC LLM để bảo đảm:
1. LLM không thể tự ý thay đổi cấp độ rủi ro (Risk Level) hoặc quyết định cấp cứu.
2. Danh sách hành động (Action Plan) chỉ được chọn lọc từ Whitelist y khoa chuẩn hóa.
3. Kích hoạt âm thanh xoa dịu phù hợp dựa trên nguyên nhân thực tế sau khi hợp nhất.
"""
import logging
from typing import List, Optional
from app.modules.cry.schemas import (
    AdjustedEvidence,
    CryContextBundle,
    CryDecision
)
from app.ai.cry_detection.sound_mapper import get_soothing_sound_url

from app.AI_agents.core.constant import CRY_ACTION_WHITELIST as ACTION_WHITELIST

logger = logging.getLogger(__name__)


class CryPolicyEngine:
    """
    Động cơ Quyết định và Thực thi Chính sách An toàn (Cry Policy Engine).
    """

    @classmethod
    def evaluate(
        cls,
        adjusted_evidence: AdjustedEvidence,
        context: CryContextBundle
    ) -> CryDecision:
        """
        Đánh giá an toàn và đưa ra CryDecision có cấu trúc nghiêm ngặt.
        """
        applied_policies: List[str] = []
        cause = adjusted_evidence.primary_cause
        confidence = adjusted_evidence.adjusted_confidence
        health = context.health

        # ── 1. SAFETY GATE: KIỂM TRA CỜ ĐỎ CẤP CỨU Y TẾ (RED FLAGS) ──
        if health and health.available and health.is_high_risk:
            applied_policies.append("SAFETY_GATE_EMERGENCY_TRIGGERED")
            return CryDecision(
                risk_level="EMERGENCY",
                primary_cause="pain",
                adjusted_confidence=max(confidence, 0.95),
                action_plan=["SEEK_EMERGENCY_CARE", "CONTACT_DOCTOR"],
                soothing_sound=None, # Tình trạng cấp cứu: không bật nhạc ru đánh lừa triệu chứng
                safety_message="🚨 CẢNH BÁO Y TẾ KHẨN CẤP: Bé có dấu hiệu sốt cao hoặc triệu chứng nguy hiểm kèm tiếng khóc đau đớn. Hãy đưa bé đến cơ sở y tế gần nhất ngay lập tức!",
                applied_policies=applied_policies
            )

        if health and health.available and health.has_fever:
            applied_policies.append("SAFETY_GATE_FEVER_MONITORING")
            return CryDecision(
                risk_level="HIGH",
                primary_cause="pain" if cause in ["pain", "discomfort"] else cause,
                adjusted_confidence=confidence,
                action_plan=["CHECK_TEMPERATURE", "CONTACT_DOCTOR", "SOOTHE"],
                soothing_sound=get_soothing_sound_url("pain"),
                safety_message="⚠️ LƯU Ý Y TẾ: Bé đang có triệu chứng sốt. Ba mẹ hãy kiểm tra thân nhiệt và chuẩn bị hạ sốt theo hướng dẫn của bác sĩ.",
                applied_policies=applied_policies
            )

        # ── 2. POLICY ENGINE: XÁC ĐỊNH HÀNH ĐỘNG DỰA TRÊN NGUYÊN NHÂN HIỆU CHỈNH ──
        risk_level = "LOW"
        action_plan: List[str] = []

        if cause == "hungry":
            applied_policies.append("POLICY_NUTRITION_FEEDING")
            action_plan = ["FEED", "SOOTHE"]
            sound = get_soothing_sound_url("hungry")

        elif cause == "burp":
            applied_policies.append("POLICY_DIGESTIVE_BURP_RELIEF")
            action_plan = ["BURP", "SOOTHE"]
            sound = get_soothing_sound_url("burp")

        elif cause == "tired":
            applied_policies.append("POLICY_SLEEP_HYGIENE_SOOTHING")
            action_plan = ["REDUCE_STIMULI", "SOOTHE"]
            sound = get_soothing_sound_url("tired")

        elif cause == "discomfort":
            applied_policies.append("POLICY_COMFORT_CHECK")
            action_plan = ["CHECK_TEMPERATURE", "BURP", "SOOTHE"]
            sound = get_soothing_sound_url("discomfort")

        elif cause == "pain":
            applied_policies.append("POLICY_PAIN_ASSESSMENT")
            risk_level = "MEDIUM"
            action_plan = ["CHECK_TEMPERATURE", "SOOTHE"]
            sound = get_soothing_sound_url("pain")

        elif cause == "scared":
            applied_policies.append("POLICY_CALMING_ENVIRONMENT")
            action_plan = ["SOOTHE", "REDUCE_STIMULI"]
            sound = get_soothing_sound_url("scared")

        elif cause == "lonely":
            applied_policies.append("POLICY_AFFECTION_CLOSENESS")
            action_plan = ["SOOTHE"]
            sound = get_soothing_sound_url("lonely")

        else:
            applied_policies.append("POLICY_DEFAULT_OBSERVATION")
            action_plan = ["SOOTHE", "CHECK_TEMPERATURE"]
            sound = get_soothing_sound_url("unknown")


        # Đảm bảo 100% action nằm trong whitelist
        validated_actions = [act for act in action_plan if act in ACTION_WHITELIST]

        return CryDecision(
            risk_level=risk_level,
            primary_cause=cause,
            adjusted_confidence=confidence,
            action_plan=validated_actions,
            soothing_sound=sound,
            safety_message=None,
            applied_policies=applied_policies
        )
