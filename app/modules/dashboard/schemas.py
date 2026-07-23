"""
Dashboard Schemas - DTOs duy nhất cho Frontend Dashboard.
Dashboard là Aggregation Module, không có domain riêng.
"""
from pydantic import BaseModel
from typing import Optional, List


# ─── Notifications ────────────────────────────────────────────────────────────

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str             # "medication" | "safety" | "feeding" | "system"
    created_at: str
    read: bool
    action_url: Optional[str] = None


# ─── Milk / Feed ─────────────────────────────────────────────────────────────

class MilkIntake(BaseModel):
    current: float        # ml đã bú trong ngày
    target: float         # ml mục tiêu (mặc định 800)
    unit: str = "ml"


# ─── Sleep ────────────────────────────────────────────────────────────────────

class SleepDuration(BaseModel):
    current: float        # phút ngủ đã tích lũy trong ngày
    target: float         # phút mục tiêu (mặc định 720 = 12h)
    unit: str = "mins"


# ─── Diaper ───────────────────────────────────────────────────────────────────

class DiaperChanges(BaseModel):
    current: int
    target: int


# ─── Medication Safety ────────────────────────────────────────────────────────

class SafetyAlert(BaseModel):
    level: str            # "NORMAL" | "CRITICAL"
    message: str

class CountdownWidget(BaseModel):
    medication_name: str
    next_eligible_time: str   # ISO 8601
    is_administer_disabled: bool


# ─── Growth Percentile ────────────────────────────────────────────────────────

class GrowthSnapshot(BaseModel):
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None
    weight_percentile: Optional[str] = None   # e.g. "50th (Normal)"
    height_percentile: Optional[str] = None


# ─── AI Tip ───────────────────────────────────────────────────────────────────

class AiTipWidget(BaseModel):
    tip_id: str
    category: str
    content: str
    scientific_reference: str


# ─── Activity Stream ──────────────────────────────────────────────────────────

class ActivityStreamItem(BaseModel):
    user: str
    action: str
    time: str
    type: str             # "feeding" | "sleep" | "medication" | "growth"


# ─── Unified Dashboard Response ───────────────────────────────────────────────

class DashboardResponse(BaseModel):
    """
    Response duy nhất cho GET /api/v1/dashboard.
    Frontend chỉ cần 1 request để lấy toàn bộ dữ liệu hiển thị.
    """
    baby_id: str
    baby_name: str

    # Widgets chính
    milk_intake: MilkIntake
    sleep_duration: SleepDuration
    diaper_changes: DiaperChanges
    nap_timer_running: bool
    last_feed_time: str

    # Sức khoẻ & thuốc
    medications_due: int
    safety_alert: Optional[SafetyAlert] = None
    countdown_widget: Optional[CountdownWidget] = None

    # Tăng trưởng
    growth_snapshot: Optional[GrowthSnapshot] = None

    # AI Tip của ngày
    ai_tip: Optional[AiTipWidget] = None

    # Dòng hoạt động (tối đa 5 mục gần nhất)
    activity_stream: List[ActivityStreamItem] = []
