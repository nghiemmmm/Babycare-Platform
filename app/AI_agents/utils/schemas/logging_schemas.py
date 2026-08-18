"""
Logging Schemas Module
======================
Pydantic contracts cho việc ghi nhận và xác thực nhật ký chăm sóc bé:
- FeedingLogSchema (Cữ bú sữa, ăn dặm)
- MedicationLogSchema (Uống thuốc, vitamin)
- SymptomLogSchema (Triệu chứng, sốt, bệnh)
- GrowthLogSchema (Chiều cao, cân nặng, vòng đầu)
"""
from typing import Optional, List
from pydantic import BaseModel, Field


class FeedingLogSchema(BaseModel):
    """Schema xác thực nhật ký ăn dặm / bú sữa của bé."""
    food_name: str = Field(..., min_length=1, description="Tên món ăn hoặc loại sữa (VD: Sữa mẹ, Sữa công thức, Cháo).")
    amount_g: float = Field(..., gt=0, description="Lượng thức ăn (gram) hoặc thể tích sữa (ml).")
    reaction: Optional[str] = Field(None, description="Phản ứng của bé (thích, nôn trớ, dị ứng...).")
    notes: Optional[str] = Field(None, description="Ghi chú thêm.")
    logged_at: Optional[str] = Field(None, description="Thời điểm ghi nhận định dạng ISO.")


class MedicationLogSchema(BaseModel):
    """Schema xác thực nhật ký uống thuốc / bổ sung vi chất."""
    medication_name: str = Field(..., min_length=1, description="Tên thuốc hoặc vitamin (VD: Hapacol, Vitamin D3 K2).")
    dosage: str = Field(..., min_length=1, description="Liều dùng cụ thể (VD: 150mg, 1 gói, 2 giọt, 5ml).")
    prescribed_by: Optional[str] = Field(None, description="Bác sĩ hoặc người kê đơn.")
    notes: Optional[str] = Field(None, description="Ghi chú thêm.")
    logged_at: Optional[str] = Field(None, description="Thời điểm ghi nhận định dạng ISO.")


class SymptomLogSchema(BaseModel):
    """Schema xác thực nhật ký triệu chứng sức khỏe."""
    symptoms: List[str] = Field(..., min_length=1, description="Danh sách các triệu chứng ghi nhận (VD: Sốt 38.5°C, Ho khan).")
    diagnosis: Optional[str] = Field(None, description="Chẩn đoán nếu có.")
    treatment: Optional[str] = Field(None, description="Phương pháp xử trí / chăm sóc.")
    doctor_name: Optional[str] = Field(None, description="Bác sĩ khám.")
    notes: Optional[str] = Field(None, description="Ghi chú thêm.")
    recorded_at: Optional[str] = Field(None, description="Thời điểm ghi nhận định dạng ISO.")


class GrowthLogSchema(BaseModel):
    """Schema xác thực chỉ số phát triển thể chất của bé."""
    height: float = Field(..., gt=0, description="Chiều cao đo được (cm).")
    weight: float = Field(..., gt=0, description="Cân nặng đo được (kg).")
    head_circumference: Optional[float] = Field(None, gt=0, description="Vòng đầu đo được (cm).")
    recorded_at: Optional[str] = Field(None, description="Thời điểm đo định dạng ISO.")
