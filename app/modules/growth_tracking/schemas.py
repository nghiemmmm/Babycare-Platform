"""
Growth Tracking Schemas Module

Defines request and response schemas for tracking baby growth.
"""
from pydantic import BaseModel, Field
from typing import Optional

class WhoGrowthStatus(BaseModel):
    age_in_months: float = Field(..., description="Tuổi của bé tính theo tháng tại thời điểm đo")
    weight_status: str = Field(..., description="Trạng thái cân nặng: underweight, normal, overweight")
    height_status: str = Field(..., description="Trạng thái chiều cao: stunted, normal, tall")
    head_circumference_status: Optional[str] = Field(None, description="Trạng thái vòng đầu: microcephaly, normal, macrocephaly")

class GrowthLogBase(BaseModel):
    height: float = Field(..., gt=0, description="Chiều cao của bé (cm)")
    weight: float = Field(..., gt=0, description="Cân nặng của bé (kg)")
    head_circumference: Optional[float] = Field(None, gt=0, description="Vòng đầu của bé (cm)")

class GrowthLogCreate(GrowthLogBase):
    pass

class GrowthLogResponse(GrowthLogBase):
    id: Optional[str] = None
    logged_at: str
    who_status: Optional[WhoGrowthStatus] = None  # Phân tích tự động từ chuẩn WHO


# Schemas mới khớp giao diện Frontend
class MeasurementCreate(BaseModel):
    baby_id: str
    weight: float
    height: float
    head_circumference: Optional[float] = None
    date: str


class Percentiles(BaseModel):
    weight_percentile: str
    height_percentile: str
    head_percentile: Optional[str] = None


class MeasurementCreateResponse(BaseModel):
    success: bool
    measurement_id: str
    percentiles: Percentiles


class MeasurementResponse(BaseModel):
    id: str
    age_months: float
    weight: float
    height: float
    head_circumference: Optional[float] = None
    date: str
