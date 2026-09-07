"""
Health Records Schemas Module

Defines request and response schemas for tracking baby health episodes,
time-series health events (symptoms, measurements, medications, care actions),
and legacy medical records.
"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


class EpisodeCategoryEnum(str, Enum):
    RESPIRATORY = "respiratory"   # Hô hấp: Ho, Sổ mũi, Khò khè, Cảm cúm
    DIGESTIVE = "digestive"       # Tiêu hóa: Tiêu chảy, Nôn trớ, Táo bón
    DERMATOLOGY = "dermatology"   # Da liễu: Chàm sữa, Mẩn ngứa, Hăm tã, Dị ứng
    TEETHING = "teething"         # Mọc răng & Quấy khóc: Sưng nướu, Chảy dãi
    FEVER = "fever"               # Sốt & Nhiễm khuẩn / Sau tiêm
    GENERAL = "general"           # Sức khỏe chung / Khác


class EventSeverityEnum(str, Enum):
    MILD = "mild"                 # Nhẹ
    MODERATE = "moderate"         # Vừa
    SEVERE = "severe"             # Nặng / Cần chú ý
    NONE = "none"                 # Đã hết / Bình thường


class EventTypeEnum(str, Enum):
    MEASUREMENT = "measurement"   # Đo lường: Thân nhiệt, Cân nặng
    SYMPTOM_CHECK = "symptom_check" # Đánh giá triệu chứng: Ho, Mũi, Phân, Da, Nướu
    MEDICATION = "medication"     # Cữ uống thuốc / Men vi sinh / Siro
    CARE_ACTION = "care_action"   # Chăm sóc: Rửa mũi, Chườm ấm, Bôi kem, Vỗ rung
    NOTE = "note"                 # Ghi nhận quan sát: Bé chịu ăn cháo, ngủ ngoan


# ============================================================================
# 1. TIME-SERIES HEALTH EVENTS (Sự kiện diễn tiến trong đợt bệnh)
# ============================================================================

class HealthEventBase(BaseModel):
    event_type: str = Field("symptom_check", description="measurement | symptom_check | medication | care_action | note")
    recorded_at: Optional[str] = Field(None, description="Thời điểm diễn ra sự kiện (ISO UTC)")
    recorded_by_name: str = Field("Phụ huynh", description="Người ghi nhận: Mẹ, Bố, Người chăm sóc")
    
    # Chỉ số định lượng
    metric_value: Optional[float] = Field(None, description="Chỉ số đo (Thân nhiệt °C, Cân nặng kg...)")
    count_value: Optional[int] = Field(None, description="Số lần đếm trong ngày (Cữ đi tiêu, Cữ nôn...)")
    
    # Chỉ số định tính & Triệu chứng
    symptom_name: Optional[str] = Field(None, description="Tên triệu chứng (Ho, Sổ mũi, Phân sống, Chàm má...)")
    severity: Optional[str] = Field(None, description="mild | moderate | severe | none")
    descriptor: Optional[str] = Field(None, description="Mô tả chi tiết (Ho có đờm sâu, Phân lỏng hoa cà, Mẩn đỏ li ti...)")
    
    # Can thiệp chăm sóc / Thuốc
    action_or_med_name: Optional[str] = Field(None, description="Tên thuốc hoặc hành động chăm sóc (Siro Prospan, Rửa mũi nước muối...)")
    notes: Optional[str] = Field(None, description="Ghi chú thêm của người chăm sóc")


class HealthEventCreate(HealthEventBase):
    pass


class HealthEventResponse(HealthEventBase):
    id: Optional[str] = None
    episode_id: Optional[str] = None


# ============================================================================
# 2. HEALTH EPISODE (Đợt theo dõi sức khỏe theo vòng đời)
# ============================================================================

class HealthEpisodeBase(BaseModel):
    category: str = Field("respiratory", description="respiratory | digestive | dermatology | teething | fever | general")
    title: str = Field(..., description="Tiêu đề đợt theo dõi (VD: Cảm cúm ho sổ mũi, Rối loạn tiêu hóa...)")
    status: str = Field("active", description="active (Đang theo dõi) | resolved (Đã khỏi bệnh)")
    progress_status: str = Field("stable", description="improving (Thuyên giảm) | stable (Ổn định) | worsening (Cần chú ý)")
    started_at: Optional[str] = Field(None, description="Thời điểm bắt đầu đợt bệnh (ISO UTC)")
    resolved_at: Optional[str] = Field(None, description="Thời điểm xác nhận khỏi bệnh (ISO UTC)")
    initial_symptoms: List[str] = Field(default_factory=list, description="Triệu chứng ban đầu khi phát hiện")
    diagnosis: Optional[str] = Field(None, description="Chẩn đoán / Tên bệnh cụ thể")
    treatment: Optional[str] = Field(None, description="Phác đồ xử lý & Hướng dẫn chăm sóc ban đầu")
    doctor_name: Optional[str] = Field(None, description="Bác sĩ khám hoặc AI Y Khoa gợi ý")
    notes: Optional[str] = Field(None, description="Ghi chú tổng quan đợt bệnh")
    primary_metric_name: Optional[str] = Field("temperature", description="Chỉ số chính: temperature | stool_count | cough_severity | rash_severity")


class HealthEpisodeCreate(HealthEpisodeBase):
    # Cho phép truyền kèm giá trị đo ban đầu
    initial_temp: Optional[float] = Field(None, description="Thân nhiệt ban đầu nếu có")
    initial_severity: Optional[str] = Field("mild", description="Mức độ nặng nhẹ ban đầu")
    initial_descriptor: Optional[str] = Field(None, description="Mô tả triệu chứng ban đầu")


class HealthEpisodeUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    progress_status: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None
    resolved_at: Optional[str] = None


class HealthEpisodeResponse(HealthEpisodeBase):
    id: Optional[str] = None
    baby_id: Optional[str] = None
    events_count: int = 0
    latest_event: Optional[HealthEventResponse] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class HealthEpisodeDetailResponse(HealthEpisodeResponse):
    events: List[HealthEventResponse] = Field(default_factory=list)
    progress_summary: Optional[str] = None


# ============================================================================
# 3. LEGACY HEALTH RECORD (Giữ nguyên tương thích ngược 100%)
# ============================================================================

class HealthRecordBase(BaseModel):
    symptoms: list[str] = Field(..., description="Danh sách các triệu chứng của bé")
    diagnosis: Optional[str] = Field(None, description="Chẩn đoán bệnh")
    treatment: Optional[str] = Field(None, description="Phương pháp điều trị, đơn thuốc")
    doctor_name: Optional[str] = Field(None, description="Tên bác sĩ khám / người kê đơn")
    notes: Optional[str] = Field(None, description="Ghi chú thêm")
    temp: Optional[float] = Field(None, description="Thân nhiệt (°C)")
    status: str = Field("Confirmed", description="Trạng thái: Confirmed (đang theo dõi) | Resolved (đã khỏi)")


class HealthRecordCreate(HealthRecordBase):
    pass


class HealthRecordUpdate(BaseModel):
    status: Optional[str] = None
    treatment: Optional[str] = None
    notes: Optional[str] = None


class HealthRecordResponse(HealthRecordBase):
    id: Optional[str] = None
    recorded_at: str
