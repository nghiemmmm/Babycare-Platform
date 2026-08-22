"""
Sleep Repository Module
=======================
Handles Firestore operations for baby sleep logs in a nested sub-collection: babies/{baby_id}/sleep_records.
"""
from app.shared.repository.base import BaseRepository
from app.modules.sleep.schemas import SleepLogResponse


class SleepRepository(BaseRepository[SleepLogResponse]):
    def __init__(self, baby_id: str):
        sub_collection_path = f"babies/{baby_id}/sleep_records"
        super().__init__(collection_name=sub_collection_path, model_class=SleepLogResponse)
