"""
Medication Service Module

Handles business logic and permission checking for medication logs.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from app.modules.medication.schemas import MedicationLogCreate, MedicationLogResponse
from app.modules.medication.repository import MedicationRepository
from app.modules.baby.service import BabyService
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

class MedicationService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def add_medication_log(self, baby_id: str, log_in: MedicationLogCreate, user_id: str) -> MedicationLogResponse:
        """
        Ghi nhận nhật ký uống thuốc mới cho bé sau khi kiểm tra quyền giám hộ.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = MedicationRepository(baby_id)
        
        log_obj = MedicationLogResponse(
            logged_at=log_in.logged_at,
            medication_name=log_in.medication_name,
            dosage=log_in.dosage,
            prescribed_by=log_in.prescribed_by,
            notes=log_in.notes
        )
        return repo.create(log_obj)

    def get_medication_history(self, baby_id: str, user_id: str) -> list[MedicationLogResponse]:
        """
        Lấy danh sách nhật ký uống thuốc của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = MedicationRepository(baby_id)
        logs = repo.list(limit=500)
        logs.sort(key=lambda x: x.logged_at, reverse=True)
        return logs

    def delete_medication_log(self, baby_id: str, log_id: str, user_id: str) -> bool:
        """
        Xóa một bản ghi nhật ký dùng thuốc.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = MedicationRepository(baby_id)
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi nhật ký dùng thuốc")
        return repo.delete(log_id)
