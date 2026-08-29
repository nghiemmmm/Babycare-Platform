"""
Medication Tracking & Management Schemas Module

Defines request and response schemas for tracking structured baby medication plans,
dose administration logs, and daily checklist schedules.
"""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal


# ============================================================================
# 1. STRUCTURED MEDICATION PLAN (Đơn thuốc / Phác đồ dùng thuốc)
# ============================================================================

class MedicationPlanBase(BaseModel):
    name: str = Field(..., description="Tên thuốc chính (ví dụ: Amoxicillin, Hapacol, Vitamin D3 K2)")
    alternative_name: Optional[str] = Field(None, description="Tên biệt dược / tên thương mại thay thế (ví dụ: Augmentin, Clamoxyl)")
    strength: Optional[str] = Field(None, description="Hàm lượng / nồng độ (ví dụ: 250 mg / 5 mL, 150mg/gói, 400IU/giọt)")
    dose: str = Field(..., description="Liều mỗi lần uống (ví dụ: 5, 1, 2, 2.5)")
    unit: str = Field("mL", description="Đơn vị tính (ví dụ: mL, gói, viên, giọt, nhát xịt)")
    route: str = Field("Oral (Đường uống)", description="Đường dùng: Oral (Đường uống), Nasal Spray (Xịt mũi), Eye Drops (Nhỏ mắt), Topical (Bôi da), Inhalation (Khí dung)")
    frequency: str = Field("1 lần/ngày", description="Tần suất dùng (ví dụ: 3 lần/ngày, 2 lần/ngày, Khi sốt > 38.5°C)")
    schedule_times: List[str] = Field(default_factory=lambda: ["08:00"], description="Các mốc giờ uống trong ngày (ví dụ: ['08:00', '14:00', '20:00'])")
    meal_timing: str = Field("after_food", description="Thời điểm so với bữa ăn: before_food (Trước ăn), after_food (Sau ăn), with_food (Cùng bữa ăn), empty_stomach (Bụng đói), anytime (Bất kỳ lúc nào), when_fever (Khi sốt)")
    start_date: str = Field(..., description="Ngày bắt đầu dùng (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Ngày kết thúc dùng (YYYY-MM-DD)")
    duration_days: Optional[int] = Field(None, description="Tổng số ngày điều trị (ví dụ: 5 ngày, 7 ngày)")
    purpose: Optional[str] = Field(None, description="Mục đích sử dụng (ví dụ: Viêm phế quản, Hạ sốt mọc răng, Bổ sung vi chất)")
    instructions: Optional[str] = Field(None, description="Lời dặn / hướng dẫn của bác sĩ (ví dụ: Pha với nước ấm, uống nhiều nước)")
    prescribed_by: Optional[str] = Field("Bác sĩ nhi khoa", description="Người kê đơn / chỉ định")
    status: Literal["active", "completed", "paused"] = Field("active", description="Trạng thái đơn: active (đang dùng), completed (đã hoàn thành), paused (tạm dừng)")


class MedicationPlanCreate(MedicationPlanBase):
    pass


class MedicationPlanUpdate(BaseModel):
    name: Optional[str] = None
    alternative_name: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    unit: Optional[str] = None
    route: Optional[str] = None
    frequency: Optional[str] = None
    schedule_times: Optional[List[str]] = None
    meal_timing: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_days: Optional[int] = None
    purpose: Optional[str] = None
    instructions: Optional[str] = None
    prescribed_by: Optional[str] = None
    status: Optional[Literal["active", "completed", "paused"]] = None


class MedicationPlanResponse(MedicationPlanBase):
    id: Optional[str] = None
    baby_id: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ============================================================================
# 2. DOSE ADMINISTRATION LOG (Lịch sử từng cữ uống)
# ============================================================================

class MedicationDoseLogBase(BaseModel):
    plan_id: Optional[str] = Field(None, description="ID đơn thuốc liên kết")
    medication_name: str = Field(..., description="Tên thuốc")
    scheduled_date: str = Field(..., description="Ngày theo lịch (YYYY-MM-DD)")
    scheduled_time: str = Field(..., description="Giờ theo lịch (HH:mm)")
    taken_at: Optional[str] = Field(None, description="Thời điểm thực tế xác nhận (ISO 8601)")
    dose_taken: str = Field("Theo chỉ định", description="Liều thực tế đã cho uống")
    status: Literal["taken", "skipped", "snoozed", "pending"] = Field("taken", description="Trạng thái cữ: taken (đã uống), skipped (bỏ qua), snoozed (hoãn lại), pending (chờ uống)")
    administered_by: str = Field("Phụ huynh", description="Người cho bé uống (Mẹ, Bố, Người giám hộ)")
    notes: Optional[str] = Field(None, description="Ghi chú phản ứng của bé khi uống")


class MedicationDoseLogCreate(MedicationDoseLogBase):
    pass


class MedicationDoseLogResponse(MedicationDoseLogBase):
    id: Optional[str] = None
    baby_id: Optional[str] = None
    created_at: Optional[str] = None


# ============================================================================
# 3. TODAY'S DYNAMIC DOSE CHECKLIST (Checklist cữ thuốc hôm nay)
# ============================================================================

class TodayDoseItem(BaseModel):
    dose_id: str
    plan_id: Optional[str] = None
    medication_name: str
    alternative_name: Optional[str] = None
    strength: Optional[str] = None
    dose_display: str
    route: str
    meal_timing: str
    scheduled_time: str
    session: Literal["morning", "afternoon", "evening", "night", "prn"]
    status: Literal["pending", "taken", "skipped"]
    taken_at: Optional[str] = None
    administered_by: Optional[str] = None
    instructions: Optional[str] = None
    purpose: Optional[str] = None


# ============================================================================
# 4. BACKWARDS COMPATIBILITY SCHEMAS
# ============================================================================

class MedicationLogBase(BaseModel):
    logged_at: Optional[str] = Field(None, description="Thời gian cho bé uống thuốc (ISO 8601)")
    medication_name: Optional[str] = Field(None, description="Tên thuốc / Vitamin bổ sung (ví dụ: Vitamin D3 K2, Hapacol)")
    name: Optional[str] = None
    dosage: str = Field("Theo chỉ định", description="Liều lượng sử dụng (ví dụ: 2 giọt, 1 gói 150mg, 5ml)")
    prescribed_by: Optional[str] = Field(None, description="Người kê đơn/chỉ định (bác sĩ Nhi, tự bổ sung...)")
    notes: Optional[str] = Field(None, description="Ghi chú thêm")
    time: Optional[str] = None
    frequency: Optional[str] = None
    active: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, values):
        if isinstance(values, dict):
            med_name = values.get("medication_name") or values.get("name") or "Thuốc/Vitamin"
            values["medication_name"] = med_name
            values["name"] = med_name
            log_time = values.get("logged_at") or values.get("created_at") or values.get("time") or "2026-08-28T09:00:00+00:00"
            values["logged_at"] = log_time
        return values


class MedicationLogCreate(MedicationLogBase):
    pass


class MedicationLogResponse(MedicationLogBase):
    id: Optional[str] = None


class SafetyAlert(BaseModel):
    level: str
    message: str


class CountdownWidget(BaseModel):
    medication_name: str
    next_eligible_time: str
    is_administer_disabled: bool


class HealthDashboardResponse(BaseModel):
    safety_alert: Optional[SafetyAlert] = None
    countdown_widget: Optional[CountdownWidget] = None


class AdministerMedicationRequest(BaseModel):
    baby_id: str
    medication_name: str
    amount: str
    administered_at: str


class AdministerMedicationResponse(BaseModel):
    success: bool
    next_scheduled_dosage: str
    countdown_seconds: int

