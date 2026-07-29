"""
Health Records Schemas Module

Defines request and response schemas for tracking baby health records.
"""
from pydantic import BaseModel, Field
from typing import Optional

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

