"""
Action Schemas Module
=====================
Defines standardized Pydantic data contracts for BabyCare Text-to-Action Pipeline:
- 4 Core Domains: Feeding, Sleep, Diaper, Medication
- Action Status & Risk Classification
- Multi-Tool Execution Reports & Clarification Contracts
"""
from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class ActionType(str, Enum):
    CREATE_FEEDING = "CREATE_FEEDING"
    CREATE_SLEEP = "CREATE_SLEEP"
    CREATE_DIAPER = "CREATE_DIAPER"
    CREATE_MEDICATION = "CREATE_MEDICATION"


class ActionRiskLevel(str, Enum):
    LOW = "LOW"       # Tự động thực thi an toàn (Feeding, Sleep, Diaper)
    HIGH = "HIGH"     # Bắt buộc qua cổng xác nhận (Medication)


class ActionStatus(str, Enum):
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    READY_TO_EXECUTE = "READY_TO_EXECUTE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"


# ─── 1. THAM SỐ CỤ THỂ CHO TỪNG DOMAIN ────────────────────────────────────────

class FeedingActionParams(BaseModel):
    amount: float = Field(..., ge=1.0, le=500.0, description="Dung tích sữa (ml) hoặc lượng thức ăn (g)")
    unit: str = Field("ml", description="ml | g | bình")
    feed_type: str = Field("Formula", description="Formula (Sữa công thức) | Breast (Sữa mẹ) | Solids (Ăn dặm)")
    food_name: Optional[str] = Field(None, description="Tên món ăn nếu là ăn dặm")
    time: Optional[str] = Field(None, description="Thời gian (HH:MM)")
    notes: Optional[str] = None


class SleepActionParams(BaseModel):
    action: str = Field("wake", description="start_sleep | wake | nap")
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440, description="Thời lượng giấc ngủ tính bằng phút")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None


class DiaperActionParams(BaseModel):
    diaper_type: str = Field("Wet", description="Wet (Tè ướt) | Dirty (Đi ngoài bẩn) | Both (Cả hai)")
    time: Optional[str] = None
    notes: Optional[str] = None


class MedicationActionParams(BaseModel):
    medication_name: str = Field(..., description="Tên thuốc hoặc vitamin (ví dụ: Hapacol 150mg, Vitamin D3 K2)")
    dosage: str = Field(..., description="Liều dùng (ví dụ: 150mg, 1 gói, 2 giọt, 5ml)")
    time: Optional[str] = None
    notes: Optional[str] = None


# ─── 2. GIAO THỨC ACTION CHUẨN TOÀN HỆ THỐNG ─────────────────────────────────

class BabyCareAction(BaseModel):
    action_id: str = Field(..., description="Mã định danh duy nhất của Action")
    action_type: ActionType
    baby_id: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: ActionRiskLevel = ActionRiskLevel.LOW
    status: ActionStatus = ActionStatus.READY_TO_EXECUTE
    requires_confirmation: bool = False
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    idempotency_key: str
    
    # Trường bổ trợ nếu thiếu thông tin
    missing_fields: List[str] = Field(default_factory=list)
    suggested_chips: List[str] = Field(default_factory=list)
    clarification_prompt: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)


class ActionResultItem(BaseModel):
    action_id: str
    action_type: ActionType
    status: ActionStatus
    record_id: Optional[str] = None
    message: str
    error: Optional[str] = None


class ActionExecutionReport(BaseModel):
    success: bool
    executed_actions: List[ActionResultItem] = Field(default_factory=list)
    pending_confirmations: List[BabyCareAction] = Field(default_factory=list)
    clarifications: List[BabyCareAction] = Field(default_factory=list)
    failed_actions: List[ActionResultItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    summary_message: Optional[str] = None


class ActionParseResponse(BaseModel):
    raw_text: str
    is_complete: bool
    parsed_actions: List[BabyCareAction] = Field(default_factory=list)
    clarifications: List[BabyCareAction] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    summary_prompt: Optional[str] = None


class ActionConfirmRequest(BaseModel):
    action: BabyCareAction
    confirmed: bool = True
