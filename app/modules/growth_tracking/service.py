"""
Growth Tracking Service Module

Handles business logic for logging and retrieving growth history of babies.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from app.modules.growth_tracking.schemas import GrowthLogCreate, GrowthLogResponse
from app.modules.growth_tracking.repository import GrowthTrackingRepository
from app.modules.baby.service import BabyService
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

class GrowthTrackingService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def add_growth_log(self, baby_id: str, log_in: GrowthLogCreate, user_id: str) -> GrowthLogResponse:
        """
        Ghi nhận chiều cao, cân nặng mới cho bé.
        Kiểm tra và xác thực quyền giám hộ trước khi ghi nhận.

        Args:
            baby_id: ID của bé.
            log_in: Dữ liệu đo đạc.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            Đối tượng GrowthLogResponse sau khi ghi nhận thành công.
        """
        # 1. Xác thực quyền giám hộ (ném lỗi 403 nếu sai)
        self.baby_service.get_baby_by_id(baby_id, user_id)

        # 2. Khởi tạo repository với path tương ứng của bé
        repo = GrowthTrackingRepository(baby_id)

        now = datetime.now(timezone.utc).isoformat()
        log_obj = GrowthLogResponse(
            height=log_in.height,
            weight=log_in.weight,
            head_circumference=log_in.head_circumference,
            logged_at=now
        )
        return repo.create(log_obj)

    def get_growth_history(self, baby_id: str, user_id: str) -> list[GrowthLogResponse]:
        """
        Lấy lịch sử phát triển chiều cao, cân nặng của bé.

        Args:
            baby_id: ID của bé.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            Danh sách lịch sử GrowthLogResponse sắp xếp mới nhất lên đầu.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = GrowthTrackingRepository(baby_id)
        logs = repo.list(limit=500)
        # Sắp xếp nhật ký mới nhất lên trước
        logs.sort(key=lambda x: x.logged_at, reverse=True)
        return logs

    def delete_growth_log(self, baby_id: str, log_id: str, user_id: str) -> bool:
        """
        Xóa một bản ghi nhật ký tăng trưởng.

        Args:
            baby_id: ID của bé.
            log_id: ID của bản ghi cần xóa.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            True nếu xóa thành công.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)

        repo = GrowthTrackingRepository(baby_id)
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi nhật ký phát triển")

        return repo.delete(log_id)
