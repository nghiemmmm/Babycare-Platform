"""
Cry Analysis Graph Module (Context-Aware Closed-Loop Pipeline)
==============================================================
Đồ thị phân tích tiếng khóc khép kín theo kiến trúc:
    detect_audio_node
           ↓
    retrieve_multi_context_node
           ↓
    explicit_fusion_node
           ↓
    safety_policy_node
           ↓
    llm_explain_node

Nguyên tắc bắt buộc:
- LLM KHÔNG PHẢI là Decision Maker.
- Toàn bộ chẩn đoán, phân loại rủi ro (Risk Level) và Kế hoạch hành động (Action Plan)
  được tính toán độc lập bởi ExplicitContextFusion và CryPolicyEngine trước khi đến LLM.
"""
import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage

from app.AI_agents.orchestrator.state_manager import OverallState
from app.AI_agents.core.reasoner import AIReasoner
from app.ai.cry_classifier import CryClassifier
from app.AI_agents.workflows.cry_context_retriever import CryContextRetriever
from app.AI_agents.core.cry_fusion_engine import ExplicitContextFusion
from app.AI_agents.core.cry_policy_engine import CryPolicyEngine
from app.modules.cry.schemas import (
    AudioEvidence,
    CryContextBundle,
    AdjustedEvidence,
    CryDecision
)
from app.AI_agents.core.constant import CRY_REASONER_PROMPT

logger = logging.getLogger(__name__)


class CryAnalysisGraph:
    """
    LangGraph Subgraph thực thi toàn bộ pipeline phân tích tiếng khóc Closed-Loop.
    """

    def __init__(self):
        from app.AI_agents.core.constant import CRY_ANALYSIS_MODEL
        self.classifier = CryClassifier()
        self.context_retriever = CryContextRetriever()
        self.reasoner = AIReasoner(model_name=CRY_ANALYSIS_MODEL)

    @property
    def nutrition_service(self):
        """Backward compatibility helper for unit tests."""
        return self.context_retriever.nutrition_service

    @property
    def health_service(self):
        """Backward compatibility helper for health service."""
        return self.context_retriever.health_service

    @property
    def medication_service(self):
        """Backward compatibility helper for medication service."""
        return self.context_retriever.medication_service

    # ── NODE 1: PHÂN TÍCH ÂM THANH BẰNG AST (AUDIO INFERENCE) ────────────────
    async def detect_audio_node(self, state: OverallState) -> dict:
        """
        Trích xuất Audio Evidence từ tệp âm thanh tiếng khóc.
        Bảo toàn 100% phân phối xác suất reason_scores và tính toán Entropy Uncertainty.
        """
        data = state.get("extracted_data") or {}
        filename = data.get("audio_file", "unknown_cry_tired.wav")

        prediction, confidence, reason_scores = self.classifier.predict(filename)
        uncertainty_score = ExplicitContextFusion.calculate_entropy_uncertainty(reason_scores)

        audio_evidence = AudioEvidence(
            top_label=prediction,
            confidence=confidence,
            reason_scores=reason_scores,
            uncertainty_score=uncertainty_score
        )

        updated_data = state.get("extracted_data", {}).copy()
        updated_data.update({
            "audio_evidence": audio_evidence.model_dump(),
            "cry_prediction": prediction,
            "cry_confidence": confidence,
            "reason_scores": reason_scores,
            "uncertainty_score": uncertainty_score
        })

        return {"extracted_data": updated_data}

    # ── NODE 2: THU THẬP ĐA NGUỒN NGỮ CẢNH (MULTI-SOURCE CONTEXT RETRIEVAL) ──
    async def retrieve_multi_context_node(self, state: OverallState) -> dict:
        """
        Truy xuất đồng thời 4 nguồn bối cảnh: Ăn dặm, Giấc ngủ, Sức khỏe/Sốt, Thuốc.
        """
        baby_id = state.get("baby_id")
        user_id = state.get("current_user_id")

        context_bundle = self.context_retriever.retrieve_bundle(baby_id, user_id)

        updated_data = state.get("extracted_data", {}).copy()
        updated_data["cry_context"] = context_bundle.model_dump()

        # Tạo chuỗi backward compatibility cho feeding_history
        feeding = context_bundle.feeding
        if feeding and feeding.available:
            feeding_str = f"Ăn dặm gần nhất: {feeding.food_name} lượng {feeding.amount_g}g vào lúc {feeding.logged_at}"
        else:
            feeding_str = "chưa có dữ liệu sinh hoạt gần đây."
        updated_data["feeding_history"] = feeding_str

        return {"extracted_data": updated_data}

    # ── NODE 3: HỢP NHẤT TƯỜNG MINH (EXPLICIT CONTEXT FUSION) ──────────────────
    async def explicit_fusion_node(self, state: OverallState) -> dict:
        """
        Điều chỉnh xác suất bằng các quy tắc logic y khoa có thể kiểm thử,
        phát hiện mâu thuẫn giữa âm thanh và bối cảnh sinh hoạt.
        """
        data = state.get("extracted_data") or {}
        raw_evidence = data.get("audio_evidence") or {}
        raw_context = data.get("cry_context") or {}

        audio_evidence = AudioEvidence(**raw_evidence) if raw_evidence else AudioEvidence(
            top_label=data.get("cry_prediction", "unknown"),
            confidence=data.get("cry_confidence", 0.0),
            reason_scores=data.get("reason_scores", {})
        )
        context_bundle = CryContextBundle(**raw_context) if raw_context else CryContextBundle()

        adjusted_evidence = ExplicitContextFusion.fuse(audio_evidence, context_bundle)

        updated_data = state.get("extracted_data", {}).copy()
        updated_data["adjusted_evidence"] = adjusted_evidence.model_dump()
        updated_data["primary_cause"] = adjusted_evidence.primary_cause
        updated_data["adjusted_confidence"] = adjusted_evidence.adjusted_confidence
        updated_data["contradiction_score"] = adjusted_evidence.contradiction_score

        return {"extracted_data": updated_data}

    # ── NODE 4: SAFETY GATE & POLICY ENGINE (PRE-LLM DECISION) ───────────────
    async def safety_policy_node(self, state: OverallState) -> dict:
        """
        Chốt chặn an toàn y tế và quyết định Action Plan + Soothing Sound trước khi gọi LLM.
        """
        data = state.get("extracted_data") or {}
        raw_adjusted = data.get("adjusted_evidence") or {}
        raw_context = data.get("cry_context") or {}

        adjusted_evidence = AdjustedEvidence(**raw_adjusted)
        context_bundle = CryContextBundle(**raw_context)

        decision = CryPolicyEngine.evaluate(adjusted_evidence, context_bundle)

        updated_data = state.get("extracted_data", {}).copy()
        updated_data["cry_decision"] = decision.model_dump()
        updated_data["soothing_sound"] = decision.soothing_sound
        updated_data["risk_level"] = decision.risk_level
        updated_data["action_plan"] = decision.action_plan

        return {"extracted_data": updated_data}

    # ── NODE 5: LLM EXPLAINER & ACTION GUIDANCE (NO DECISION MAKING) ─────────
    async def llm_explain_node(self, state: OverallState) -> dict:
        """
        LLM chỉ làm nhiệm vụ GIẢI THÍCH và HƯỚNG DẪN HÀNH ĐỘNG dựa trên Decision đã xác định.
        """
        data = state.get("extracted_data") or {}
        raw_decision = data.get("cry_decision") or {}
        raw_adjusted = data.get("adjusted_evidence") or {}
        raw_context = data.get("cry_context") or {}

        decision = CryDecision(**raw_decision)
        adjusted_evidence = AdjustedEvidence(**raw_adjusted)
        context = CryContextBundle(**raw_context)

        # Định dạng bối cảnh sinh hoạt ngắn gọn
        feeding = context.feeding
        feeding_sum = f"{feeding.food_name} ({feeding.amount_g}g), cách đây {feeding.minutes_since_feed} phút" if feeding.available else "Không có dữ liệu cữ ăn gần đây"

        sleep = context.sleep
        sleep_sum = f"Đã thức {sleep.wake_window_minutes} phút (ngủ dậy lúc {sleep.wake_time})" if sleep.available else "Không có dữ liệu giấc ngủ gần đây"

        health = context.health
        health_sum = f"Nhiệt độ: {health.temperature}°C, Triệu chứng: {', '.join(health.symptoms) or 'Không có'}" if health.available else "Chưa ghi nhận triệu chứng bệnh bất thường"

        med = context.medication
        med_sum = f"Uống {med.medication_name} ({med.dosage}) cách đây {med.minutes_since_medication} phút" if med.available else "Chưa có nhật ký dùng thuốc gần đây"

        # Định dạng phân phối điểm âm thanh
        scores_str = ", ".join([f"{k}: {int(v*100)}%" for k, v in list(adjusted_evidence.adjusted_scores.items())[:4]])

        instruction = CRY_REASONER_PROMPT.format(
            primary_cause=decision.primary_cause,
            adjusted_confidence=int(decision.adjusted_confidence * 100),
            risk_level=decision.risk_level,
            action_plan=", ".join(decision.action_plan),
            reason_scores_str=scores_str,
            applied_rules=", ".join(adjusted_evidence.applied_rules),
            safety_message=decision.safety_message or "Không có cảnh báo khẩn cấp",
            feeding_summary=feeding_sum,
            sleep_summary=sleep_sum,
            health_summary=health_sum,
            medication_summary=med_sum
        )

        try:
            explanation = await self.reasoner.areason(
                prompt=f"Hãy giải thích vì sao bé khóc do {decision.primary_cause} và hướng dẫn phụ huynh thực hiện các hành động: {', '.join(decision.action_plan)}.",
                system_instruction=instruction
            )
        except Exception as e:
            logger.error(f"[CryAnalysisGraph] LLM explanation error: {e}")
            explanation = (
                f"Hệ thống xác định nguyên nhân bé khóc là: {decision.primary_cause} "
                f"(độ tin cậy: {int(decision.adjusted_confidence * 100)}%). "
                f"Khuyến nghị hành động: {', '.join(decision.action_plan)}."
            )

        # Cấu trúc phản hồi hoàn chỉnh
        sound_text = f"\n- Âm thanh vỗ về đề xuất: {decision.soothing_sound}" if decision.soothing_sound else ""
        safety_header = f"🚨 [{decision.safety_message}]\n\n" if decision.risk_level == "EMERGENCY" else ""
        
        full_message = (
            f"{safety_header}🤖 [Chẩn đoán tiếng khóc - Phân tích Closed-Loop]\n"
            f"- Nguyên nhân chính: {decision.primary_cause} ({int(decision.adjusted_confidence * 100)}%)\n"
            f"- Cấp độ rủi ro: {decision.risk_level}\n"
            f"- Kế hoạch hành động: {', '.join(decision.action_plan)}{sound_text}\n\n"
            f"Lời khuyên & Hướng dẫn chi tiết:\n{explanation}"
        )

        updated_data = state.get("extracted_data", {}).copy()
        updated_data["llm_explanation"] = explanation
        updated_data["advice"] = full_message

        return {
            "messages": [AIMessage(content=full_message)],
            "extracted_data": updated_data
        }

    # ── BACKWARD COMPATIBILITY NODES CHO TEST CŨ ────────────────────────────
    async def detect_cry_node(self, state: OverallState) -> dict:
        """Legacy compatibility wrapper."""
        return await self.detect_audio_node(state)

    async def context_aggregator_node(self, state: OverallState) -> dict:
        """Legacy compatibility wrapper."""
        return await self.retrieve_multi_context_node(state)

    async def reason_cry_node(self, state: OverallState) -> dict:
        """Legacy compatibility wrapper."""
        # Chạy qua fusion -> policy -> llm
        state1 = await self.explicit_fusion_node(state)
        state_merged = state.copy()
        state_merged["extracted_data"] = state1["extracted_data"]
        
        state2 = await self.safety_policy_node(state_merged)
        state_merged["extracted_data"] = state2["extracted_data"]
        
        return await self.llm_explain_node(state_merged)

    # ── BIÊN DỊCH LANGGRAPH ĐỒ THỊ ──────────────────────────────────────────
    def compile(self, checkpointer=None):
        """Compile the complete 5-node closed-loop pipeline."""
        builder = StateGraph(OverallState)
        
        builder.add_node("detect_audio", self.detect_audio_node)
        builder.add_node("retrieve_multi_context", self.retrieve_multi_context_node)
        builder.add_node("explicit_fusion", self.explicit_fusion_node)
        builder.add_node("safety_policy", self.safety_policy_node)
        builder.add_node("llm_explain", self.llm_explain_node)

        builder.add_edge(START, "detect_audio")
        builder.add_edge("detect_audio", "retrieve_multi_context")
        builder.add_edge("retrieve_multi_context", "explicit_fusion")
        builder.add_edge("explicit_fusion", "safety_policy")
        builder.add_edge("safety_policy", "llm_explain")
        builder.add_edge("llm_explain", END)

        return builder.compile(checkpointer=checkpointer)
