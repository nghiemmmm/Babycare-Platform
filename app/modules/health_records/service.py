"""
Health Records Service Module

Handles business logic for logging and retrieving medical history of babies.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from app.modules.health_records.schemas import HealthRecordCreate, HealthRecordResponse
from app.modules.health_records.repository import HealthRecordRepository
from app.modules.baby.service import BabyService
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

class HealthRecordService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def add_record(self, baby_id: str, record_in: HealthRecordCreate, user_id: str) -> HealthRecordResponse:
        """
        Thêm một bệnh án mới cho bé sau khi xác thực quyền giám hộ.

        Args:
            baby_id: ID của bé.
            record_in: Dữ liệu bệnh án mới.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            Đối tượng HealthRecordResponse đã lưu.
        """
        # Xác thực quyền giám hộ
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = HealthRecordRepository(baby_id)
        now = datetime.now(timezone.utc).isoformat()
        record_obj = HealthRecordResponse(
            symptoms=record_in.symptoms,
            diagnosis=record_in.diagnosis,
            treatment=record_in.treatment,
            doctor_name=record_in.doctor_name,
            notes=record_in.notes,
            recorded_at=now
        )
        return repo.create(record_obj)

    def get_history(self, baby_id: str, user_id: str) -> list[HealthRecordResponse]:
        """
        Lấy toàn bộ lịch sử bệnh án của bé (Yêu cầu quyền giám hộ).

        Args:
            baby_id: ID của bé.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            Danh sách bệnh án HealthRecordResponse sắp xếp mới nhất lên đầu.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = HealthRecordRepository(baby_id)
        records = repo.list(limit=500)
        # Sắp xếp bản ghi mới nhất lên trước
        records.sort(key=lambda x: x.recorded_at, reverse=True)
        return records

    def delete_record(self, baby_id: str, record_id: str, user_id: str) -> bool:
        """
        Xóa một bản ghi bệnh án khỏi hệ thống.

        Args:
            baby_id: ID của bé.
            record_id: ID của bản ghi bệnh án cần xóa.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            True nếu xóa thành công.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = HealthRecordRepository(baby_id)
        record = repo.get(record_id)
        if not record:
            raise EntityNotFoundError("Không tìm thấy thông tin bệnh án cần xóa")

        return repo.delete(record_id)
