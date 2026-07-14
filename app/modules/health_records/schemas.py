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
    doctor_name: Optional[str] = Field(None, description="Tên bác sĩ khám")
    notes: Optional[str] = Field(None, description="Ghi chú thêm")


class HealthRecordCreate(HealthRecordBase):
    pass


class HealthRecordResponse(HealthRecordBase):
    id: Optional[str] = None
    recorded_at: str
