"""
AI Cry Tracking Schemas Module

Defines request and response schemas for tracking baby cry logs, multi-context evidence,
deterministic decision policy, and outcome-aware feedback.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


# ─── 1. AUDIO EVIDENCE SCHEMAS ───────────────────────────────────────────────

class AudioEvidence(BaseModel):
    top_label: str = Field(..., description="Nhãn phân loại có điểm cao nhất từ mô hình AST")
    confidence: float = Field(..., description="Độ tin cậy của nhãn cao nhất (0.0 - 1.0)")
    reason_scores: Dict[str, float] = Field(default_factory=dict, description="Phân phối xác suất của toàn bộ các nguyên nhân khóc")
    uncertainty_score: float = Field(0.0, description="Độ bất định chuẩn hóa Entropy H(p)/log(N) (0.0: chắc chắn tuyệt đối, 1.0: hoàn toàn phân tán)")


# ─── 2. MULTI-SOURCE CONTEXT SCHEMAS ─────────────────────────────────────────

class FeedingContext(BaseModel):
    available: bool = False
    food_name: Optional[str] = None
    amount_g: Optional[float] = None
    logged_at: Optional[str] = None
    minutes_since_feed: Optional[int] = None
    reaction: Optional[str] = None


class SleepContext(BaseModel):
    available: bool = False
    last_sleep_time: Optional[str] = None
    wake_time: Optional[str] = None
    wake_window_minutes: Optional[int] = None
    sleep_duration_minutes: Optional[int] = None


class HealthContext(BaseModel):
    available: bool = False
    temperature: Optional[float] = None
    symptoms: List[str] = Field(default_factory=list)
    diagnosis: Optional[str] = None
    recorded_at: Optional[str] = None
    has_fever: bool = False
    is_high_risk: bool = False


class MedicationContext(BaseModel):
    available: bool = False
    medication_name: Optional[str] = None
    dosage: Optional[str] = None
    logged_at: Optional[str] = None
    minutes_since_medication: Optional[int] = None


class CryContextBundle(BaseModel):
    baby_id: Optional[str] = None
    retrieved_at: Optional[str] = None
    feeding: FeedingContext = Field(default_factory=FeedingContext)
    sleep: SleepContext = Field(default_factory=SleepContext)
    health: HealthContext = Field(default_factory=HealthContext)
    medication: MedicationContext = Field(default_factory=MedicationContext)


# ─── 3. FUSION & DECISION SCHEMAS ───────────────────────────────────────────

class AdjustedEvidence(BaseModel):
    adjusted_scores: Dict[str, float] = Field(default_factory=dict)
    primary_cause: str
    adjusted_confidence: float
    contradiction_score: float = Field(0.0, description="Mức độ mâu thuẫn giữa âm thanh và bối cảnh sinh hoạt (0.0: đồng thuận, 1.0: mâu thuẫn đối kháng)")
    applied_rules: List[str] = Field(default_factory=list)


class CryDecision(BaseModel):
    risk_level: str = Field("LOW", description="Mức độ rủi ro: LOW | MEDIUM | HIGH | EMERGENCY")
    primary_cause: str = Field(..., description="Nguyên nhân kết luận cuối cùng sau khi đã hợp nhất ngữ cảnh")
    adjusted_confidence: float = Field(..., description="Độ tin cậy của kết luận sau hiệu chỉnh")
    action_plan: List[str] = Field(default_factory=list, description="Kế hoạch hành động chuẩn hóa từ whitelist")
    soothing_sound: Optional[str] = Field(None, description="Đường dẫn âm thanh xoa dịu được chỉ định")
    safety_message: Optional[str] = Field(None, description="Thông điệp an toàn hoặc cảnh báo y tế khẩn cấp")
    applied_policies: List[str] = Field(default_factory=list)


# ─── 4. FEEDBACK & OUTCOME SCHEMAS ──────────────────────────────────────────

class CryFeedbackUpdate(BaseModel):
    feedback_accurate: Optional[bool] = Field(None, description="Đánh giá từ phụ huynh xem AI đoán đúng hay sai")
    actual_cause: Optional[str] = Field(None, description="Nguyên nhân thực tế được phụ huynh xác nhận")
    soothed: Optional[bool] = Field(None, description="Bé có nín khóc sau can thiệp không")
    soothed_after_minutes: Optional[int] = Field(None, description="Số phút bé nín khóc sau khi áp dụng hướng dẫn")
    intervention_used: Optional[str] = Field(None, description="Hành động phụ huynh thực tế đã áp dụng")
    parent_notes: Optional[str] = Field(None, description="Ghi chú thêm từ phụ huynh")


class CryOutcomeRecord(BaseModel):
    log_id: str
    baby_id: str
    logged_at: str
    audio_evidence: AudioEvidence
    context: CryContextBundle
    decision: CryDecision
    feedback: Optional[CryFeedbackUpdate] = None


# ─── 5. DATABASE & REST API RESPONSE SCHEMAS ────────────────────────────────

class CryLogBase(BaseModel):
    logged_at: str = Field(..., description="Thời điểm bé khóc (ISO 8601)")
    audio_url: str = Field(..., description="Đường dẫn lưu trữ tệp ghi âm tiếng khóc (.wav, .mp3)")
    
    # Kết quả chẩn đoán cơ bản (backward compatibility)
    prediction: str = Field(..., description="Nguyên nhân chính: hungry, tired, pain, burp, discomfort, v.v.")
    confidence: float = Field(..., description="Độ tin cậy của dự đoán chính (0.0 - 1.0)")
    reason_scores: Optional[Dict[str, float]] = Field(None, description="Chi tiết phân phối xác suất các nguyên nhân")
    
    # Dữ liệu mở rộng Closed-Loop
    audio_evidence: Optional[AudioEvidence] = None
    context: Optional[CryContextBundle] = None
    decision: Optional[CryDecision] = None
    advice: Optional[str] = None
    
    # Phản hồi từ phụ huynh & Kích hoạt âm thanh vỗ về
    feedback_accurate: Optional[bool] = Field(None, description="Đánh giá từ phụ huynh xem AI đoán đúng hay sai")
    feedback_details: Optional[CryFeedbackUpdate] = None
    sound_conditioned: bool = Field(False, description="Đã tự động kích hoạt âm thanh vỗ về hay chưa")
    sound_played: Optional[str] = Field(None, description="Tên âm thanh/nhạc đã phát")
    notes: Optional[str] = Field(None, description="Ghi chú bổ sung")


class CryLogCreate(CryLogBase):
    pass


class CryLogResponse(CryLogBase):
    id: Optional[str] = None
