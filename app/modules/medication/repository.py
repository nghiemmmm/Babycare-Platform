"""
Medication Tracking Repository Module

Handles Firestore operations for baby medication logs in a nested sub-collection.
"""
from app.shared.repository.base import BaseRepository
from app.modules.medication.schemas import MedicationLogResponse

class MedicationRepository(BaseRepository[MedicationLogResponse]):
    def __init__(self, baby_id: str):
        # Đường dẫn sub-collection trên Firestore: babies/{baby_id}/medication_logs
        sub_collection_path = f"babies/{baby_id}/medication_logs"
        super().__init__(collection_name=sub_collection_path, model_class=MedicationLogResponse)
