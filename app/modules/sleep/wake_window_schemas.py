"""
Wake Window Prediction Schemas Module
=====================================
Pydantic Schemas bám sát Bằng sáng chế US 20250292903:
- Group A: Current baby information (age, nap_number)
- Group B: Current-day temporal features (day_start, previous_night_end)
- Group C: Recent wake-window history (previous_wake_window, prior wake windows)
- Group D: Recent nap history (previous_nap, previous_sleep_duration, previous_wake_duration)
- Group E: Recent 5-day history representation
- Group F: Project-derived extensions & API response models
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. Biểu diễn Ma trận 5 Ngày Gần Nhất (Recent 5-Day History Representation)
# [DIRECTLY SUPPORTED BY PATENT]
# ---------------------------------------------------------------------------
class SingleDaySleepRepresentation(BaseModel):
    day_offset: int = Field(..., description="Khoảng cách ngày: -1 (hôm qua), -2 (2 ngày trước)... đến -5")
    wake_windows_minutes: List[int] = Field(default_factory=list, description="Danh sách các wake windows trong ngày đó [WW1, WW2...]")
    naps_duration_minutes: List[int] = Field(default_factory=list, description="Thời lượng từng giấc nap ngày đó [Nap1, Nap2...]")
    night_sleep_duration_minutes: Optional[int] = Field(None, description="Thời lượng giấc ngủ đêm (phút)")
    day_start_minutes: Optional[int] = Field(None, description="Giờ bắt đầu ngày tính từ 00:00 (phút)")


class Last5DaysHistoryRepresentation(BaseModel):
    days: List[SingleDaySleepRepresentation] = Field(default_factory=list, description="Tập hợp biểu diễn từ Day -5 đến Day -1")
    # Project-derived statistics [PROJECT IMPLEMENTATION]
    avg_wake_window_minutes: float = Field(..., description="Trung bình toàn bộ wake windows trong 5 ngày")
    std_wake_window_minutes: float = Field(default=12.0, description="Độ lệch chuẩn thời gian thức")
    avg_nap_duration_minutes: float = Field(default=60.0, description="Thời lượng giấc nap trung bình")
    avg_night_sleep_hours: float = Field(default=11.0, description="Số giờ ngủ đêm trung bình")
    avg_naps_count_per_day: float = Field(default=3.0, description="Số giấc ngày trung bình")


# ---------------------------------------------------------------------------
# 2. Vector Đặc trưng Đầu vào Tổng hợp (Model Feature Input Vector)
# [DIRECTLY SUPPORTED BY PATENT] & [PROJECT IMPLEMENTATION]
# ---------------------------------------------------------------------------
class WakeWindowFeatureVector(BaseModel):
    # Group A: Current Baby Information [DIRECTLY SUPPORTED BY PATENT]
    age_months: float = Field(..., ge=0, description="Tuổi của bé theo tháng (ví dụ: 6.5)")
    age_days: int = Field(..., ge=0, description="Tuổi của bé tính theo ngày")
    nap_number: int = Field(..., ge=1, description="Thứ tự giấc nap cần dự đoán (1, 2, 3...)")

    # Group B: Current-Day Temporal Features [DIRECTLY SUPPORTED BY PATENT]
    day_start_minutes: int = Field(..., description="Thời điểm bắt đầu ngày tính bằng số phút từ 00:00")
    previous_night_end_minutes: int = Field(..., description="Thời điểm kết thúc đêm trước tính bằng số phút từ 00:00")

    # Group C: Recent Wake-Window History [DIRECTLY SUPPORTED BY PATENT]
    previous_wake_window_minutes: int = Field(..., description="Khoảng thời gian thức ngay trước đó (phút)")
    prior_wake_windows_today: List[int] = Field(default_factory=list, description="Các khoảng thức trước đó trong ngày hôm nay")

    # Group D: Recent Nap History [DIRECTLY SUPPORTED BY PATENT]
    previous_nap_minutes: int = Field(..., description="Thời lượng giấc nap vừa xong (0 nếu là Nap 1)")
    previous_sleep_duration_minutes: int = Field(..., description="Thời lượng ngủ liền trước (ngủ đêm nếu Nap 1, nap trước nếu Nap 2+)")
    previous_wake_duration_minutes: int = Field(default=0, description="Thời gian bé thực tế đã thức đến lúc query")

    # Group E: Recent 5-Day History [DIRECTLY SUPPORTED BY PATENT]
    last_5_days_history: Optional[Last5DaysHistoryRepresentation] = None

    # Group F: Project-Derived Extensions [PROJECT IMPLEMENTATION]
    is_first_nap: int = Field(default=0, description="1 nếu là Nap 1 của ngày")
    is_bedtime_nap: int = Field(default=0, description="1 nếu là giấc ngủ trước Bedtime")
    is_catnap: int = Field(default=0, description="1 nếu giấc trước < 35 phút")
    is_long_nap: int = Field(default=0, description="1 nếu giấc trước >= 90 phút")
    data_days_available: int = Field(default=0, ge=0, le=5, description="Số ngày có dữ liệu thực tế (0 đến 5)")


# ---------------------------------------------------------------------------
# 3. Request & Response API Models
# [PROJECT IMPLEMENTATION]
# ---------------------------------------------------------------------------
class WakeWindowPredictionResponse(BaseModel):
    baby_id: str = Field(..., description="ID của em bé")
    predicted_wake_window_minutes: int = Field(..., description="Khoảng thời gian thức tối ưu dự đoán (phút)")
    predicted_wake_window_formatted: str = Field(..., description="Định dạng thân thiện: X giờ Y phút")
    optimal_sleep_time: str = Field(..., description="Thời điểm vàng đặt bé ngủ (HH:MM)")
    wind_down_start_time: str = Field(..., description="Thời điểm bắt đầu chuẩn bị phòng ngủ (HH:MM)")
    model_source: str = Field(
        ..., 
        description="'LIGHTGBM_NORMAL' | 'EXPERT_VALUE_PLUS_LLM' | 'EXPERT_BASELINE_COLD_START' | 'LIGHTGBM_CLAMPED'"
    )
    is_anomaly_case: bool = Field(default=False, description="True nếu ML rơi vào nhánh bất thường và kích hoạt LLM")
    anomaly_reason: Optional[str] = Field(None, description="Lý do bất thường và phân tích lâm sàng nếu có")
    parental_guidance: Optional[str] = Field(None, description="Lời dặn dò ấm áp, tinh tế dành cho phụ huynh")
    data_days_available: int = Field(..., description="Số ngày dữ liệu lịch sử đã được sử dụng")
    features_summary: Dict[str, Any] = Field(default_factory=dict, description="Tóm tắt các đặc trưng quan trọng đã dùng")
