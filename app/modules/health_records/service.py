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

    def generate_ai_treatment(self, symptoms: list[str], diagnosis: Optional[str] = None, baby_name: str = "bé") -> str:
        """
        AI Backend Generator: Tự động sinh phác đồ chăm sóc y tế thông minh dựa trên chẩn đoán & triệu chứng.
        """
        parts = []
        sym_text = (" ".join(symptoms) + " " + (diagnosis or "")).lower()

        # Quy tắc thân nhiệt & hạ sốt
        if "sốt" in sym_text:
            if "39.5" in sym_text or "sốt cao" in sym_text:
                parts.append("⚠️ Sốt cao: Cho uống Paracetamol 10-15mg/kg (theo chỉ dẫn), chườm ấm trán nách bẹn và đưa bé đến cơ sở y tế nếu sốt kéo dài >48h.")
            else:
                parts.append("Chườm ấm trán nách, giữ phòng thoáng mát, uống nhiều nước/sữa và theo dõi thân nhiệt mỗi 30 phút.")

        # Quy tắc đường hô hấp
        if any(w in sym_text for w in ["ho", "họng", "cảm"]):
            parts.append("Dùng siro ho thảo dược nhi khoa, nhỏ mũi nước muối sinh lý 0.9% và giữ ấm cổ.")
        if any(w in sym_text for w in ["sổ mũi", "ngạt"]):
            parts.append("Làm sạch dịch mũi bằng dụng cụ chuyên dụng và duy trì độ ẩm phòng 55-60%.")

        # Quy tắc tiêu hóa
        if any(w in sym_text for w in ["nôn", "tiêu chảy", "bụng"]):
            parts.append("Cho uống Oresol bù điện giải rải rác trong ngày và ăn thức ăn lỏng dễ tiêu.")

        # Quy tắc mọc răng & da liễu
        if any(w in sym_text for w in ["mọc răng", "nướu", "dãi"]):
            parts.append("Cho ngậm nướu lạnh và mát-xa nướu nhẹ nhàng.")
        if any(w in sym_text for w in ["mẩn", "dị ứng", "ban"]):
            parts.append("Giữ da sạch thoáng, tắm nước ấm dịu nhẹ và tránh chất gây kích ứng.")

        if not parts:
            parts.append(f"Cho {baby_name} nghỉ ngơi, theo dõi sinh hoạt và bổ sung đầy đủ dinh dưỡng/nước.")

        return " ".join(parts)

    def add_record(self, baby_id: str, record_in: HealthRecordCreate, user_id: str) -> HealthRecordResponse:
        """
        Thêm một bệnh án mới cho bé sau khi xác thực quyền giám hộ.
        """
        # Xác thực quyền giám hộ & lấy thông tin bé
        baby = self.baby_service.get_baby_by_id(baby_id, user_id)
        baby_name = baby.name if baby else "bé"

        # Nếu chưa có phác đồ điều trị, Backend tự động kích hoạt AI Generator
        treatment = record_in.treatment
        if not treatment:
            treatment = self.generate_ai_treatment(
                symptoms=record_in.symptoms,
                diagnosis=record_in.diagnosis,
                baby_name=baby_name
            )

        repo = HealthRecordRepository(baby_id)
        now = datetime.now(timezone.utc).isoformat()
        record_obj = HealthRecordResponse(
            symptoms=record_in.symptoms,
            diagnosis=record_in.diagnosis,
            treatment=treatment,
            doctor_name=record_in.doctor_name or "AI Y Khoa Gợi Ý",
            notes=record_in.notes,
            temp=record_in.temp,
            status=record_in.status or "Confirmed",
            recorded_at=now
        )
        return repo.create(record_obj)

    def get_history(self, baby_id: str, user_id: str) -> list[HealthRecordResponse]:
        """
        Lấy toàn bộ lịch sử bệnh án của bé (Yêu cầu quyền giám hộ).
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = HealthRecordRepository(baby_id)
        records = repo.list(limit=500)
        # Sắp xếp bản ghi mới nhất lên trước
        records.sort(key=lambda x: x.recorded_at, reverse=True)
        return records

    def update_record(self, baby_id: str, record_id: str, update_data: dict, user_id: str) -> HealthRecordResponse:
        """
        Cập nhật thông tin bệnh án (ví dụ đổi trạng thái Confirmed -> Resolved).
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = HealthRecordRepository(baby_id)
        existing = repo.get(record_id)
        if not existing:
            raise EntityNotFoundError("Không tìm thấy thông tin bệnh án cần cập nhật")
        return repo.update(record_id, update_data)

    def delete_record(self, baby_id: str, record_id: str, user_id: str) -> bool:
        """
        Xóa một bản ghi bệnh án khỏi hệ thống.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = HealthRecordRepository(baby_id)
        record = repo.get(record_id)
        if not record:
            raise EntityNotFoundError("Không tìm thấy thông tin bệnh án cần xóa")

        return repo.delete(record_id)

