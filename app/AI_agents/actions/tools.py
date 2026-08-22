"""
Action Tools Implementation Module
==================================
Encapsulates tool execution for the 4 Core Domains.
STRICT ARCHITECTURAL RULE: Every tool MUST call its respective Business Service.
NO direct Firestore access is permitted in this layer.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from app.AI_agents.actions.schemas import (
    ActionType,
    ActionStatus,
    ActionResultItem,
    FeedingActionParams,
    SleepActionParams,
    DiaperActionParams,
    MedicationActionParams
)
from app.modules.nutrition.feed_service import FeedService
from app.modules.nutrition.service import SolidFoodService
from app.modules.nutrition.schemas import FeedCreate, SolidFoodLogCreate
from app.modules.sleep.service import SleepService
from app.modules.sleep.schemas import SleepLogCreate
from app.modules.medication.service import MedicationService
from app.modules.medication.schemas import MedicationLogCreate

logger = logging.getLogger(__name__)


class BaseActionTool:
    action_type: ActionType

    async def execute(self, action_id: str, baby_id: str, parameters: Dict[str, Any], user_id: str) -> ActionResultItem:
        raise NotImplementedError


class FeedingActionTool(BaseActionTool):
    action_type = ActionType.CREATE_FEEDING

    def __init__(self, feed_service: Optional[FeedService] = None, solid_service: Optional[SolidFoodService] = None):
        self.feed_service = feed_service or FeedService()
        self.solid_service = solid_service or SolidFoodService()

    async def execute(self, action_id: str, baby_id: str, parameters: Dict[str, Any], user_id: str) -> ActionResultItem:
        try:
            params = FeedingActionParams(**parameters)
            feed_type = params.feed_type
            amount = params.amount
            now_time = params.time or datetime.now(timezone.utc).strftime("%H:%M")

            if feed_type == "Solids":
                food_name = params.food_name or "Ăn dặm dinh dưỡng"
                log = self.solid_service.add_solid_food_log(
                    baby_id=baby_id,
                    log_in=SolidFoodLogCreate(
                        food_name=food_name,
                        amount_g=amount,
                        notes=params.notes
                    ),
                    user_id=user_id
                )
                record_id = log.id
                msg = f"Đã ghi nhận cữ ăn dặm '{food_name}' ({int(amount)}g)"
            else:
                type_name = "Sữa mẹ" if feed_type == "Breast" else "Sữa công thức"
                details = f"{int(amount)}ml {type_name}"
                res = self.feed_service.add_feed_log(
                    baby_id=baby_id,
                    feed_in=FeedCreate(
                        baby_id=baby_id,
                        type=type_name,
                        amount=amount,
                        details=details,
                        time=now_time
                    ),
                    user_id=user_id
                )
                record_id = res.feed_id
                msg = f"Đã ghi nhận cữ bú {int(amount)}ml {type_name}"

            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                record_id=record_id,
                message=msg
            )
        except Exception as e:
            logger.error(f"[FeedingActionTool] Error: {e}")
            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                message=f"Lỗi ghi nhận cữ bú: {str(e)}",
                error=str(e)
            )


class SleepActionTool(BaseActionTool):
    action_type = ActionType.CREATE_SLEEP

    def __init__(self, sleep_service: Optional[SleepService] = None):
        self.sleep_service = sleep_service or SleepService()

    async def execute(self, action_id: str, baby_id: str, parameters: Dict[str, Any], user_id: str) -> ActionResultItem:
        try:
            params = SleepActionParams(**parameters)
            now = datetime.now(timezone.utc)
            
            # Tự động tính toán mốc thời gian bắt đầu và kết thúc chu kỳ ngủ
            end_time = params.end_time
            start_time = params.start_time
            if params.action == "wake":
                end_time = end_time or now.isoformat()
                if params.duration_minutes and not start_time:
                    start_dt = now - timedelta(minutes=params.duration_minutes)
                    start_time = start_dt.isoformat()

            log = self.sleep_service.add_sleep_log(
                baby_id=baby_id,
                log_in=SleepLogCreate(
                    action=params.action,
                    duration_minutes=params.duration_minutes,
                    start_time=start_time,
                    end_time=end_time,
                    notes=params.notes
                ),
                user_id=user_id
            )
            dur_str = f" ({params.duration_minutes} phút)" if params.duration_minutes else ""
            act_str = "bắt đầu ngủ" if params.action == "start_sleep" else f"thức dậy{dur_str}"
            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                record_id=log.id,
                message=f"Đã ghi nhận giấc ngủ: Bé {act_str}"
            )

        except Exception as e:
            logger.error(f"[SleepActionTool] Error: {e}")
            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                message=f"Lỗi ghi nhận giấc ngủ: {str(e)}",
                error=str(e)
            )


class DiaperActionTool(BaseActionTool):
    action_type = ActionType.CREATE_DIAPER

    def __init__(self, feed_service: Optional[FeedService] = None):
        self.feed_service = feed_service or FeedService()

    async def execute(self, action_id: str, baby_id: str, parameters: Dict[str, Any], user_id: str) -> ActionResultItem:
        try:
            params = DiaperActionParams(**parameters)
            diaper_type = params.diaper_type
            type_desc = "Tè ướt" if diaper_type == "Wet" else ("Đi ngoài bẩn" if diaper_type == "Dirty" else "Thay tã đầy đủ")
            now_time = params.time or datetime.now(timezone.utc).strftime("%H:%M")
            
            # Ghi nhận hoạt động thay tã vào feed timeline
            res = self.feed_service.add_feed_log(
                baby_id=baby_id,
                feed_in=FeedCreate(
                    baby_id=baby_id,
                    type="Thay tã",
                    amount=0.0,
                    details=f"Thay tã: {type_desc}",
                    time=now_time
                ),
                user_id=user_id
            )
            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                record_id=res.feed_id,
                message=f"Đã ghi nhận thay tã ({type_desc})"
            )
        except Exception as e:
            logger.error(f"[DiaperActionTool] Error: {e}")
            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                message=f"Lỗi ghi nhận thay tã: {str(e)}",
                error=str(e)
            )


class MedicationActionTool(BaseActionTool):
    action_type = ActionType.CREATE_MEDICATION

    def __init__(self, med_service: Optional[MedicationService] = None):
        self.med_service = med_service or MedicationService()

    async def execute(self, action_id: str, baby_id: str, parameters: Dict[str, Any], user_id: str) -> ActionResultItem:
        try:
            params = MedicationActionParams(**parameters)
            log = self.med_service.add_medication_log(
                baby_id=baby_id,
                log_in=MedicationLogCreate(
                    medication_name=params.medication_name,
                    dosage=params.dosage,
                    notes=params.notes
                ),
                user_id=user_id
            )
            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.COMPLETED,
                record_id=log.id,
                message=f"Đã ghi nhận cữ uống thuốc '{params.medication_name}' ({params.dosage})"
            )
        except Exception as e:
            logger.error(f"[MedicationActionTool] Error: {e}")
            return ActionResultItem(
                action_id=action_id,
                action_type=self.action_type,
                status=ActionStatus.FAILED,
                message=f"Lỗi ghi nhận uống thuốc: {str(e)}",
                error=str(e)
            )
