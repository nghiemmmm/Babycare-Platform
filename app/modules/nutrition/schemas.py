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


# Schemas cho tính năng gợi ý dinh dưỡng AI (RAG, cá nhân hoá theo dị ứng/bệnh lý)
class FoodRecommendationItem(BaseModel):
    food_name: str
    reason: str

class FoodAvoidanceItem(BaseModel):
    food_name: str
    reason: str
    linked_to: str  # Tên dị ứng/bệnh lý cụ thể gắn với lý do tránh món này

class NutritionRecommendationResponse(BaseModel):
    id: Optional[str] = None
    baby_id: str
    generated_at: str
    recommended_foods: list[FoodRecommendationItem]
    foods_to_avoid: list[FoodAvoidanceItem]
    summary: str
    based_on_allergies: list[str]
    based_on_conditions: list[str]


# Schemas cho thực đơn ăn dặm 7 ngày (RAG, có state pending/accepted + khoá tạo mới)
class MealSlot(BaseModel):
    meal_type: str  # "sáng" | "trưa" | "tối" | "phụ"
    food_name: str
    note: Optional[str] = None

class DayPlan(BaseModel):
    date: str  # YYYY-MM-DD - ngày thật, server tự tính từ hôm nay
    meals: list[MealSlot]

class WeeklyMealPlanResponse(BaseModel):
    id: Optional[str] = None
    baby_id: str
    generated_at: str
    start_date: str
    end_date: str
    status: str = "pending"  # "pending" | "accepted"
    accepted_at: Optional[str] = None
    days: list[DayPlan]
    summary: str
    based_on_allergies: list[str]
    based_on_conditions: list[str]

class GenerateWeeklyMealPlanRequest(BaseModel):
    baby_id: str
    feedback: Optional[str] = Field(
        None, description="Phản hồi của phụ huynh khi tạo lại (vd: bé không thích cá, tránh món cay)"
    )
