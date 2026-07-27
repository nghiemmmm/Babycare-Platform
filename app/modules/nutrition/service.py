"""
Solid Food Service Module

Handles business logic and permission checking for solid food logs.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from app.modules.nutrition.schemas import SolidFoodLogCreate, SolidFoodLogResponse
from app.modules.nutrition.repository import SolidFoodRepository
from app.modules.baby.service import BabyService
from app.modules.guardian.permissions import ADMIN, GUARDIAN, require_role
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)

class SolidFoodService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def add_solid_food_log(self, baby_id: str, log_in: SolidFoodLogCreate, user_id: str) -> SolidFoodLogResponse:
        """
        Ghi nhận nhật ký ăn dặm mới cho bé sau khi kiểm tra quyền giám hộ.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        repo = SolidFoodRepository(baby_id)

        log_obj = SolidFoodLogResponse(
            logged_at=log_in.logged_at,
            food_name=log_in.food_name,
            amount_g=log_in.amount_g,
            reaction=log_in.reaction,
            notes=log_in.notes
        )
        return repo.create(log_obj)

    def get_solid_food_history(self, baby_id: str, user_id: str) -> list[SolidFoodLogResponse]:
        """
        Lấy lịch sử ăn dặm của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = SolidFoodRepository(baby_id)
        logs = repo.list(limit=500)
        logs.sort(key=lambda x: x.logged_at, reverse=True)
        return logs

    def delete_solid_food_log(self, baby_id: str, log_id: str, user_id: str) -> bool:
        """
        Xóa một bản ghi nhật ký ăn dặm.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        repo = SolidFoodRepository(baby_id)
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi nhật ký ăn dặm")
        return repo.delete(log_id)
