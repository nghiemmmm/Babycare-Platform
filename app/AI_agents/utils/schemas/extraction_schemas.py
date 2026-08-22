"""
Extraction Schemas Module
=========================
Pydantic contracts cho Tier 0 Fast Extraction & Deterministic DB Lookup:
- FastExtractionData (Dữ liệu bóc tách nhanh qua regex/pure python)
- ActivityTypeEnum (Danh sách các loại hoạt động / truy vấn tra cứu)
"""
from enum import Enum
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class ActivityTypeEnum(str, Enum):
    """Phân loại hoạt động bóc tách từ ngôn ngữ tự nhiên."""
    GREETING = "greeting"
    FEEDING = "feeding"
    MEDICATION = "medication"
    GROWTH = "growth"
    SYMPTOM = "symptom"
    READ_LAST_FEED = "read_last_feed"
    READ_LAST_MEDICATION = "read_last_medication"
    READ_TODAY_MILK = "read_today_milk"
    READ_GROWTH_PROFILE = "read_growth_profile"
    READ_CARE_SCHEDULE = "read_care_schedule"
    CREATE_CARE_TASK = "create_care_task"


class FastExtractionData(BaseModel):
    """
    Schema kết quả bóc tách nhanh tại Tier 0 (Pure Code < 5ms).
    """
    activity_type: str = Field(..., description="Mã loại hoạt động hoặc tra cứu (greeting, feeding, read_last_feed...).")
    food_name: Optional[str] = Field(None, description="Tên món ăn / sữa.")
    amount_g: Optional[int] = Field(None, description="Số lượng hoặc dung tích.")
    unit: Optional[str] = Field(None, description="Đơn vị tính (ml, g, bình...).")
    medication_name: Optional[str] = Field(None, description="Tên thuốc.")
    dosage: Optional[str] = Field(None, description="Liều dùng thuốc.")
    height: Optional[float] = Field(None, description="Chiều cao đo được (cm).")
    weight: Optional[float] = Field(None, description="Cân nặng đo được (kg).")
    temperature: Optional[float] = Field(None, description="Nhiệt độ cơ thể (°C).")
    symptoms: List[str] = Field(default_factory=list, description="Danh sách triệu chứng bóc tách được.")
    scheduled_time: Optional[str] = Field(None, description="Mốc thời gian đặt lịch (HH:MM hoặc ISO).")
    assigned_to_name: Optional[str] = Field(None, description="Tên người được gán thực hiện.")
    task_title: Optional[str] = Field(None, description="Tiêu đề việc cần làm.")
    instructions: Optional[str] = Field(None, description="Lời dặn chi tiết.")

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển đổi sang dict loại bỏ các trường None."""
        return self.model_dump(exclude_none=True)
