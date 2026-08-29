"""
Medication Tracking & Management Repository Module

Handles Firestore operations for baby medication plans, dose logs, and legacy medication logs.
"""
from app.shared.repository.base import BaseRepository
from app.modules.medication.schemas import (
    MedicationLogResponse,
    MedicationPlanResponse,
    MedicationDoseLogResponse
)

class MedicationRepository(BaseRepository[MedicationLogResponse]):
    def __init__(self, baby_id: str):
        sub_collection_path = f"babies/{baby_id}/medication_logs"
        super().__init__(collection_name=sub_collection_path, model_class=MedicationLogResponse)


class MedicationPlanRepository(BaseRepository[MedicationPlanResponse]):
    def __init__(self, baby_id: str):
        sub_collection_path = f"babies/{baby_id}/medication_plans"
        super().__init__(collection_name=sub_collection_path, model_class=MedicationPlanResponse)


class MedicationDoseLogRepository(BaseRepository[MedicationDoseLogResponse]):
    def __init__(self, baby_id: str):
        sub_collection_path = f"babies/{baby_id}/medication_dose_logs"
        super().__init__(collection_name=sub_collection_path, model_class=MedicationDoseLogResponse)

