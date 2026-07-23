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


# Schemas mới khớp giao diện Frontend
class FeedCreate(BaseModel):
    baby_id: str
    type: str
    details: str
    amount: float
    time: str

class FeedResponse(BaseModel):
    id: str
    type: str
    details: str
    amount: float
    time: str

class FeedCreateResponse(BaseModel):
    success: bool
    feed_id: str

class IngredientCreate(BaseModel):
    baby_id: str
    name: str
    reaction: str

class IngredientResponse(BaseModel):
    id: str
    name: str
    reaction: str
    date: str

class IngredientCreateResponse(BaseModel):
    success: bool
    ingredient_log_id: str

class SuccessResponse(BaseModel):
    success: bool
    message: Optional[str] = None

class FoodSafetyItemResponse(BaseModel):
    name: str
    reason: str
    category: str = "under_1_year"
    min_age_months: int = 12

class AllergenAlertResponse(BaseModel):
    allergens: list[str] = Field(default_factory=list)
    warning_message: str = ""
    has_alert: bool = False

class NutritionSafetyResponse(BaseModel):
    foods_to_avoid: list[FoodSafetyItemResponse]
    allergen_alerts: AllergenAlertResponse

class SafetyHandbookSection(BaseModel):
    title: str
    description: str
    items: Optional[list[str]] = None
    level: str = "info"

class SafetyHandbookResponse(BaseModel):
    title: str = "Cẩm nang An toàn Dinh dưỡng (WHO/AAP)"
    sections: list[SafetyHandbookSection]
