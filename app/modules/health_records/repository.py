"""
Health Records Repository Module

Handles Firestore collection operations for baby health records in a nested sub-collection.
"""
from app.shared.repository.base import BaseRepository
from app.modules.health_records.schemas import HealthRecordResponse

class HealthRecordRepository(BaseRepository[HealthRecordResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/health_records
        sub_collection_path = f"babies/{baby_id}/health_records"
        super().__init__(collection_name=sub_collection_path, model_class=HealthRecordResponse)
