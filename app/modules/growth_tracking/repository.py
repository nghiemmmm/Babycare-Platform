"""
Growth Tracking Repository Module

Handles Firestore operations for baby growth logs in a nested sub-collection.
"""
from app.shared.repository.base import BaseRepository
from app.modules.growth_tracking.schemas import GrowthLogResponse

class GrowthTrackingRepository(BaseRepository[GrowthLogResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/growth_logs
        sub_collection_path = f"babies/{baby_id}/growth_logs"
        super().__init__(collection_name=sub_collection_path, model_class=GrowthLogResponse)
