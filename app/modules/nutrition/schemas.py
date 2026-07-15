"""
Solid Food Tracking Schemas Module

Defines request and response schemas for tracking baby solid food consumption.
"""
from pydantic import BaseModel, Field
from typing import Optional

class SolidFoodLogBase(BaseModel):
    logged_at: str = Field(..., description="Thời gian bé ăn dặm (ISO 8601)")
    food_name: str = Field(..., description="Tên món ăn dặm (ví dụ: Cháo bơ, Bột yến mạch)")
    amount_g: Optional[float] = Field(None, description="Lượng ăn dặm (gram hoặc ml)")
    reaction: Optional[str] = Field(None, description="Phản ứng của bé: like (thích), dislike (ghét), allergic (dị ứng), vomit (trớ)")
    notes: Optional[str] = Field(None, description="Ghi chú thêm")

class SolidFoodLogCreate(SolidFoodLogBase):
    pass

class SolidFoodLogResponse(SolidFoodLogBase):
    id: Optional[str] = None
