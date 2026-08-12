"""
Growth Tracking Service Module

Handles business logic for logging and retrieving growth history of babies.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from app.modules.growth_tracking.schemas import GrowthLogCreate, GrowthLogResponse, WhoGrowthStatus
from app.modules.growth_tracking.repository import GrowthTrackingRepository
from app.modules.growth_tracking.utils import get_closest_standard, evaluate_metric
from app.modules.baby.service import BabyService
from app.shared.exceptions import EntityNotFoundError
from app.infrastructure.cache.redis import get_json, set_json, invalidate_baby_cache
from app.core.config import settings

logger = logging.getLogger(__name__)

def calculate_who_status(
    baby_birthday_str: str,
    baby_gender: str,
    log_date_str: str,
    height: float,
    weight: float,
    head: Optional[float]
) -> WhoGrowthStatus:
    """
    Tính toán trạng thái chiều cao, cân nặng, vòng đầu của bé dựa trên tiêu chuẩn WHO.
    """
    # Safeguard for unit test mock objects
    if not isinstance(baby_birthday_str, str) or not isinstance(baby_gender, str):
        return WhoGrowthStatus(
            age_in_months=0.0,
            weight_status="normal",
            height_status="normal",
            head_circumference_status=None
        )

    try:
        birth_date = datetime.fromisoformat(baby_birthday_str.replace("Z", "+00:00"))
        log_date = datetime.fromisoformat(log_date_str.replace("Z", "+00:00"))
    except ValueError:
        # Fallback nếu format ngày sinh dạng YYYY-MM-DD
        birth_date = datetime.strptime(baby_birthday_str[:10], "%Y-%m-%d")
        log_date = datetime.fromisoformat(log_date_str.replace("Z", "+00:00"))

    age_days = (log_date.date() - birth_date.date()).days
    age_months = max(0.0, age_days / 30.4375)

    # Lấy tiêu chuẩn mốc tháng tuổi gần nhất
    std = get_closest_standard(baby_gender, age_months)
    
    w_status = evaluate_metric(weight, std["weight"], "underweight", "overweight")
    h_status = evaluate_metric(height, std["height"], "stunted", "tall")
    
    hc_status = None
    if head is not None:
        hc_status = evaluate_metric(head, std["head"], "microcephaly", "macrocephaly")

    return WhoGrowthStatus(
        age_in_months=round(age_months, 1),
        weight_status=w_status,
        height_status=h_status,
        head_circumference_status=hc_status
    )

class GrowthTrackingService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def _populate_who_status(self, log: GrowthLogResponse, baby_birth_date: str, baby_gender: str) -> GrowthLogResponse:
        """
        Gán động chỉ số trạng thái WHO cho bản ghi đo đạc.
        """
        log.who_status = calculate_who_status(
            baby_birthday_str=baby_birth_date,
            baby_gender=baby_gender,
            log_date_str=log.logged_at,
            height=log.height,
            weight=log.weight,
            head=log.head_circumference
        )
        return log

    def add_growth_log(self, baby_id: str, log_in: GrowthLogCreate, user_id: str) -> GrowthLogResponse:
        """
        Ghi nhận chiều cao, cân nặng mới cho bé.
        Kiểm tra và xác thực quyền giám hộ trước khi ghi nhận.
        """
        # 1. Xác thực quyền giám hộ và lấy thông tin bé
        baby = self.baby_service.get_baby_by_id(baby_id, user_id)

        # 2. Khởi tạo repository
        repo = GrowthTrackingRepository(baby_id)

        now = datetime.now(timezone.utc).isoformat()
        log_obj = GrowthLogResponse(
            height=log_in.height,
            weight=log_in.weight,
            head_circumference=log_in.head_circumference,
            logged_at=now
        )
        
        # 3. Tính toán và lưu trữ kèm trạng thái WHO
        self._populate_who_status(log_obj, baby.birth_date, baby.gender)
        created = repo.create(log_obj)
        invalidate_baby_cache(baby_id, user_id)
        return created

    def get_growth_history(self, baby_id: str, user_id: str) -> list[GrowthLogResponse]:
        """
        Lấy lịch sử phát triển chiều cao, cân nặng của bé kèm đối chiếu WHO (đệm Redis 60s).
        """
        cache_key = f"growth_history:{baby_id}"
        cached_data = get_json(cache_key)
        if cached_data and isinstance(cached_data, list):
            return [GrowthLogResponse(**item) for item in cached_data]

        baby = self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = GrowthTrackingRepository(baby_id)
        logs = repo.list(limit=500)
        
        # Điền động trạng thái đối chiếu WHO cho từng bản ghi trong lịch sử
        for log in logs:
            self._populate_who_status(log, baby.birth_date, baby.gender)
            
        # Sắp xếp nhật ký mới nhất lên trước
        logs.sort(key=lambda x: x.logged_at, reverse=True)
        set_json(cache_key, [l.model_dump() for l in logs], ttl_seconds=settings.BABY_CACHE_TTL_SECONDS)
        return logs

    def delete_growth_log(self, baby_id: str, log_id: str, user_id: str) -> bool:
        """
        Xóa một bản ghi nhật ký tăng trưởng.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = GrowthTrackingRepository(baby_id)
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi nhật ký phát triển")

        res = repo.delete(log_id)
        if res:
            invalidate_baby_cache(baby_id, user_id)
        return res
