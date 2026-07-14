"""
Vaccination Service Module

Handles business logic for generating vaccine schedule and updating vaccination status.
"""
import logging
import math
import calendar
from datetime import datetime, timedelta, timezone
from typing import Optional
from app.modules.vaccination.schemas import VaccinationUpdate, VaccinationResponse
from app.modules.vaccination.repository import VaccinationRepository
from app.modules.baby.service import BabyService
from app.infrastructure.database import get_firestore_db
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

def _add_months(source_date: datetime, months: float) -> datetime:
    """Hàm bổ trợ cộng thêm số tháng (kể cả số lẻ) vào ngày chỉ định."""
    fraction, whole = math.modf(months)
    
    # Cộng phần tháng nguyên
    month = source_date.month - 1 + int(whole)
    year = source_date.year + month // 12
    month = month % 12 + 1
    day = min(source_date.day, calendar.monthrange(year, month)[1])
    
    base_date = datetime(year, month, day)
    
    # Cộng phần tháng lẻ quy đổi sang ngày (1 tháng tương đương 30 ngày)
    if fraction > 0:
        base_date += timedelta(days=int(fraction * 30))
        
    return base_date

class VaccinationService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def generate_default_schedule(self, baby_id: str, birth_date_str: str) -> None:
        """
        Tự động tạo lịch trình tiêm chủng dự kiến dựa trên danh mục vaccines mẫu.
        """
        try:
            db = get_firestore_db()
            # 1. Đọc danh mục vaccine gốc
            vaccines = db.collection("vaccines").stream()
            
            repo = VaccinationRepository(baby_id)
            birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
            
            for doc in vaccines:
                v_data = doc.to_dict()
                recommended_months = v_data.get("recommended_age_months", 0)
                
                # Tính ngày tiêm dự kiến
                scheduled_date = _add_months(birth_date, recommended_months)
                scheduled_date_str = scheduled_date.strftime("%Y-%m-%d")
                
                vaccination = VaccinationResponse(
                    id=doc.id,
                    vaccine_code=doc.id,
                    vaccine_name=v_data.get("name", ""),
                    scheduled_date=scheduled_date_str,
                    status="scheduled"
                )
                # Lưu vào Firestore
                repo.create(vaccination, doc_id=doc.id)
                
            logger.info(f"Generated default vaccine schedule for baby ID: {baby_id}")
        except Exception as e:
            logger.error(f"Failed to generate vaccine schedule: {e}")
            raise e

    def get_baby_vaccinations(self, baby_id: str, user_id: str) -> list[VaccinationResponse]:
        """
        Lấy toàn bộ lịch tiêm chủng của bé (Yêu cầu quyền giám hộ).
        """
        # Xác thực quyền giám hộ
        self.baby_service.get_baby_by_id(baby_id, user_id)
        
        repo = VaccinationRepository(baby_id)
        schedule = repo.list(limit=100)
        # Sắp xếp theo ngày tiêm dự kiến tăng dần
        schedule.sort(key=lambda x: x.scheduled_date)
        return schedule

    def update_vaccination_status(
        self, baby_id: str, vaccine_code: str, data_in: VaccinationUpdate, user_id: str
    ) -> VaccinationResponse:
        """
        Cập nhật trạng thái một mũi tiêm (Đã tiêm / Quá hạn / Ghi chú).
        """
        # Xác thực quyền giám hộ
        self.baby_service.get_baby_by_id(baby_id, user_id)
        
        repo = VaccinationRepository(baby_id)
        
        # Kiểm tra tồn tại bản ghi
        record = repo.get(vaccine_code)
        if not record:
            raise EntityNotFoundError(f"Không tìm thấy thông tin mũi tiêm {vaccine_code}")
            
        data = data_in.model_dump(exclude_unset=True)
        updated = repo.update(vaccine_code, data)
        if not updated:
            raise EntityNotFoundError("Cập nhật trạng thái tiêm thất bại")
            
        return updated
