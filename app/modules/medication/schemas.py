"""
Medication Tracking Schemas Module

Defines request and response schemas for tracking baby medication logs.
"""
from pydantic import BaseModel, Field
from typing import Optional

class MedicationLogBase(BaseModel):
    logged_at: str = Field(..., description="Thời gian cho bé uống thuốc (ISO 8601)")
    medication_name: str = Field(..., description="Tên thuốc / Vitamin bổ sung (ví dụ: Vitamin D3 K2, Hapacol)")
    dosage: str = Field(..., description="Liều lượng sử dụng (ví dụ: 2 giọt, 1 gói 150mg, 5ml)")
    prescribed_by: Optional[str] = Field(None, description="Người kê đơn/chỉ định (bác sĩ Nhi, tự bổ sung...)")
    notes: Optional[str] = Field(None, description="Ghi chú thêm")

class MedicationLogCreate(MedicationLogBase):
    pass

class MedicationLogResponse(MedicationLogBase):
    id: Optional[str] = None
