"""
AI Cry Tracking Repository Module

Handles Firestore operations for baby cry logs in a nested sub-collection.
"""
from app.shared.repository.base import BaseRepository
from app.modules.cry.schemas import CryLogResponse

class CryRepository(BaseRepository[CryLogResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/cry_logs
        sub_collection_path = f"babies/{baby_id}/cry_logs"
        super().__init__(collection_name=sub_collection_path, model_class=CryLogResponse)
