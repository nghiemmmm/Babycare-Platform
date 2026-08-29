from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MessageCreateRequest(BaseModel):
    message: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = "text"
    thread_id: Optional[str] = None
    baby_id: Optional[str] = None

    @property
    def text_content(self) -> str:
        return (self.content or self.message or "").strip()


class Citation(BaseModel):
    title: str
    source: Optional[str] = None
    uri: Optional[str] = None
    content: Optional[str] = None

class ExtractedLog(BaseModel):
    type: str  # "feeding" | "medication" | "growth" | "sleep" | "diaper" | "unknown"
    data: dict

class ToolStep(BaseModel):
    id: str
    tool_name: str
    display_name: str
    args: dict = {}
    status: str = "completed"  # "pending" | "running" | "completed" | "failed"
    result_summary: Optional[str] = None
    start_time: str
    duration_ms: Optional[int] = None

class MessageResponseDetails(BaseModel):
    citations: List[Citation] = []
    extracted_log: Optional[ExtractedLog] = None
    tool_steps: List[ToolStep] = []

class MessageCreateResponse(BaseModel):
    thread_id: str
    reply: str
    details: MessageResponseDetails

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None
    baby_id: Optional[str] = None

class ChatResponse(BaseModel):
    thread_id: Optional[str] = None
    reply: Optional[str] = None
    response: Optional[str] = None
    next_step: Optional[str] = None
    citations: List[Citation] = []
    extracted_log: Optional[ExtractedLog] = None
    tool_steps: List[ToolStep] = []


class ThreadResponse(BaseModel):
    thread_id: str
    id: Optional[str] = None
    created_at: str
    updated_at: str
    title: Optional[str] = "Cuộc trò chuyện mới"
    baby_id: Optional[str] = None
    last_updated: Optional[str] = None


class ThreadCreateResponse(BaseModel):
    thread_id: str
    id: Optional[str] = None
    title: str = "Cuộc trò chuyện mới"
    created_at: Optional[str] = None


class SleepTimerRequest(BaseModel):
    baby_id: str
    action: str  # "start" | "stop" | "status"

class SleepTimerResponse(BaseModel):
    baby_id: str
    is_running: bool
    started_at: Optional[str] = None
    elapsed_seconds: int = 0
    message: str

class ChatMessageResponse(BaseModel):
    id: str
    role: str  # "user" / "assistant"
    content: str
    timestamp: str
    tool_steps: List[ToolStep] = []


# ─── CANONICAL SCHEMAS CHO VOICE AUTOFILL FORM ───────────────────────────────

class CanonicalFeedingData(BaseModel):
    food_name: Optional[str] = None
    amount: Optional[float] = Field(None, ge=1.0, le=500.0, description="Lượng sữa/thức ăn (ml hoặc g)")
    unit: str = Field("ml", description="ml | g | bình")
    feed_type: str = Field("Formula", description="Formula | Breast | Solids")
    details: Optional[str] = None

class CanonicalMedicationData(BaseModel):
    medication_name: str
    dosage: str
    unit: Optional[str] = None
    frequency: Optional[str] = None

class CanonicalGrowthData(BaseModel):
    weight: Optional[float] = Field(None, ge=1.0, le=40.0, description="Cân nặng (kg)")
    height: Optional[float] = Field(None, ge=30.0, le=150.0, description="Chiều cao (cm)")
    head_circumference: Optional[float] = None

class CanonicalDiaperData(BaseModel):
    type: str = Field("Wet", description="Wet | Dirty | Both")
    details: Optional[str] = None

class CanonicalSleepData(BaseModel):
    action: str = Field("wake", description="start_sleep | wake | nap")
    duration_minutes: Optional[int] = None
    details: Optional[str] = None


class VoiceExtractRequest(BaseModel):
    transcript: str
    baby_id: Optional[str] = None

class VoiceExtractResponse(BaseModel):
    success: bool = True
    intent: str = Field(..., description="feeding | medication | diaper | sleep | unknown")
    confidence: float = Field(1.0, ge=0.0, le=1.0)

    extracted_data: Dict[str, Any] = Field(default_factory=dict, description="Dữ liệu bóc tách thô (backward compatibility)")
    canonical_data: Dict[str, Any] = Field(default_factory=dict, description="Dữ liệu cấu trúc chuẩn hóa cho Form")
    missing_fields: List[str] = Field(default_factory=list, description="Danh sách các trường cần phụ huynh xác nhận/chọn thêm")
    suggested_chips: List[str] = Field(default_factory=list, description="Các gợi ý 1-tap để hoàn tất nhanh trên giao diện")
    warnings: List[str] = Field(default_factory=list, description="Cảnh báo số liệu bất thường hoặc câu phủ định")
    confidence_message: str = "Bóc tách dữ liệu từ giọng nói thành công."
