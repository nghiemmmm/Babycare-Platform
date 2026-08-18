"""
Explicit Context Fusion Engine
==============================
Hợp nhất tường minh giữa Bằng chứng Sóng âm (Audio Evidence) và Bối cảnh Sinh hoạt Đời thực (CryContextBundle).
Hoạt động hoàn toàn bằng quy tắc toán học và logic y khoa xác định (Deterministic Rule-Based),
KHÔNG sử dụng LLM ở tầng này để đảm bảo tính an toàn, có thể kiểm thử và truy vết tuyệt đối.
"""
import math
import logging
from typing import Dict, List, Tuple
from app.modules.cry.schemas import (
    AudioEvidence,
    CryContextBundle,
    AdjustedEvidence
)

from app.AI_agents.core.constant import (
    RECENT_FEED_THRESHOLD_MINUTES,
    HUNGER_STARVATION_THRESHOLD_MINUTES,
    TIRED_WAKE_WINDOW_THRESHOLD_MINUTES,
    OVERTIRED_WAKE_WINDOW_THRESHOLD_MINUTES,
    HIGH_FEVER_THRESHOLD,
    PENALTY_RECENT_FEED,
    BOOST_BURP_AFTER_FEED,
    BOOST_DISCOMFORT_AFTER_FEED,
    BOOST_HUNGER_LONG_FAST,
    BOOST_TIRED_LONG_WAKE,
    BOOST_PAIN_FEVER
)

logger = logging.getLogger(__name__)


class ExplicitContextFusion:
    """
    Động cơ Hợp nhất Ngữ cảnh Tường minh (Explicit Fusion Engine).
    """

    @staticmethod
    def calculate_entropy_uncertainty(scores: Dict[str, float]) -> float:
        """
        Tính độ bất định phân phối xác suất Entropy chuẩn hóa: H(p) / log2(N)
        Kết quả: 0.0 (chắc chắn tuyệt đối vào 1 nhãn) -> 1.0 (hoàn toàn phân tán đều).
        """
        if not scores:
            return 1.0
        
        values = [max(1e-6, float(v)) for v in scores.values() if float(v) > 0]
        total = sum(values)
        probs = [v / total for v in values]
        n_classes = max(len(probs), 2)
        
        entropy = -sum(p * math.log2(p) for p in probs)
        max_entropy = math.log2(n_classes)
        normalized = entropy / max_entropy if max_entropy > 0 else 0.0
        return round(min(1.0, max(0.0, normalized)), 4)

    @classmethod
    def fuse(
        cls,
        audio_evidence: AudioEvidence,
        context: CryContextBundle
    ) -> AdjustedEvidence:
        """
        Hợp nhất AudioEvidence và CryContextBundle theo các luật logic nhi khoa.
        """
        applied_rules: List[str] = []
        contradiction_score: float = 0.0
        
        # Sao chép phân phối điểm ban đầu từ Audio Evidence
        scores = {k: max(0.01, float(v)) for k, v in (audio_evidence.reason_scores or {}).items()}
        if not scores:
            scores = {audio_evidence.top_label: audio_evidence.confidence}

        # Đảm bảo các nhãn cơ bản luôn có trong phân phối
        for label in ["hungry", "tired", "pain", "burp", "discomfort", "lonely", "cold_hot", "scared"]:
            if label not in scores:
                scores[label] = 0.02

        # ── LUẬT 1: MÂU THUẪN VỪA ĂN XONG NHƯNG ÂM THANH BÁO ĐÓI (FEEDING CONTRADICTION) ──
        feeding = context.feeding
        if feeding and feeding.available and feeding.minutes_since_feed is not None:
            mins = feeding.minutes_since_feed
            if mins <= RECENT_FEED_THRESHOLD_MINUTES:
                # Nếu mô hình âm thanh đoán đói hoặc điểm đói cao
                if audio_evidence.top_label == "hungry" or scores.get("hungry", 0) >= 0.35:
                    applied_rules.append("RECENT_FEED_CONTRADICTS_HUNGER")
                    contradiction_score = max(contradiction_score, 0.85)
                    # Phạt điểm hungry, tăng điểm burp và discomfort
                    scores["hungry"] = max(0.02, scores.get("hungry", 0) - PENALTY_RECENT_FEED)
                    scores["burp"] = scores.get("burp", 0) + BOOST_BURP_AFTER_FEED
                    scores["discomfort"] = scores.get("discomfort", 0) + BOOST_DISCOMFORT_AFTER_FEED
            elif mins >= HUNGER_STARVATION_THRESHOLD_MINUTES:
                applied_rules.append("LONG_FASTING_CONFIRMS_HUNGER")
                scores["hungry"] = scores.get("hungry", 0) + BOOST_HUNGER_LONG_FAST

        # ── LUẬT 2: THỜI GIAN THỨC KÉO DÀI CỦNG CỐ TIẾNG KHÓC GẮT NGỦ (SLEEP ALIGNMENT) ──
        sleep = context.sleep
        if sleep and sleep.available and sleep.wake_window_minutes is not None:
            wake_mins = sleep.wake_window_minutes
            if wake_mins >= TIRED_WAKE_WINDOW_THRESHOLD_MINUTES:
                applied_rules.append("LONG_WAKE_WINDOW_BOOSTS_TIRED")
                scores["tired"] = scores.get("tired", 0) + BOOST_TIRED_LONG_WAKE
                if wake_mins >= OVERTIRED_WAKE_WINDOW_THRESHOLD_MINUTES:
                    applied_rules.append("OVERTIRED_STATE_DETECTED")
                    scores["discomfort"] = scores.get("discomfort", 0) + 0.20

        # ── LUẬT 3: SỐT CAO / BỆNH LÝ CỦNG CỐ NGUYÊN NHÂN ĐAU (HEALTH RISK ALIGNMENT) ──
        health = context.health
        if health and health.available:
            if health.has_fever or health.is_high_risk:
                applied_rules.append("HEALTH_FEVER_OR_SYMPTOM_BOOSTS_PAIN")
                scores["pain"] = scores.get("pain", 0) + BOOST_PAIN_FEVER
                contradiction_score = max(contradiction_score, 0.50) if audio_evidence.top_label == "tired" else contradiction_score

        # ── CHUẨN HÓA LẠI PHÂN PHỐI ĐIỂM (L1 PROBABILITY NORMALIZATION) ──
        total_score = sum(scores.values())
        adjusted_scores = {k: round(v / total_score, 4) for k, v in scores.items()}
        sorted_scores = dict(sorted(adjusted_scores.items(), key=lambda x: x[1], reverse=True))

        # Trích xuất nhãn dẫn đầu sau hiệu chỉnh
        primary_cause = list(sorted_scores.keys())[0]
        adjusted_confidence = sorted_scores[primary_cause]

        if not applied_rules:
            applied_rules.append("AUDIO_EVIDENCE_DOMINANT")

        return AdjustedEvidence(
            adjusted_scores=sorted_scores,
            primary_cause=primary_cause,
            adjusted_confidence=adjusted_confidence,
            contradiction_score=round(contradiction_score, 2),
            applied_rules=applied_rules
        )
