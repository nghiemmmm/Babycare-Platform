"""
Solid Food Tracking Repository Module

Handles Firestore operations for baby solid food logs in a nested sub-collection.
"""
from app.shared.repository.base import BaseRepository
from app.modules.nutrition.schemas import SolidFoodLogResponse, NutritionRecommendationResponse, WeeklyMealPlanResponse

class SolidFoodRepository(BaseRepository[SolidFoodLogResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/solid_food_logs
        sub_collection_path = f"babies/{baby_id}/solid_food_logs"
        super().__init__(collection_name=sub_collection_path, model_class=SolidFoodLogResponse)


class NutritionRecommendationRepository(BaseRepository[NutritionRecommendationResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/nutrition_recommendations
        # Luôn dùng doc_id="latest" - đây là gợi ý hiện tại, không phải lịch sử tích luỹ.
        sub_collection_path = f"babies/{baby_id}/nutrition_recommendations"
        super().__init__(collection_name=sub_collection_path, model_class=NutritionRecommendationResponse)


class WeeklyMealPlanRepository(BaseRepository[WeeklyMealPlanResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/weekly_meal_plans
        # Luôn dùng doc_id="latest" - đây là thực đơn tuần hiện tại, không phải lịch sử tích luỹ.
        sub_collection_path = f"babies/{baby_id}/weekly_meal_plans"
        super().__init__(collection_name=sub_collection_path, model_class=WeeklyMealPlanResponse)
