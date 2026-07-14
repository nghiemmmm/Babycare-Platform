"""
Growth Tracking Schemas Module

Defines request and response schemas for tracking baby growth.
"""
from pydantic import BaseModel, Field
from typing import Optional

class GrowthLogBase(BaseModel):
    height: float = Field(..., gt=0, description="Chiều cao của bé (cm)")
    weight: float = Field(..., gt=0, description="Cân nặng của bé (kg)")
    head_circumference: Optional[float] = Field(None, gt=0, description="Vòng đầu của bé (cm)")


class GrowthLogCreate(GrowthLogBase):
    pass


class GrowthLogResponse(GrowthLogBase):
    id: Optional[str] = None
    logged_at: str
