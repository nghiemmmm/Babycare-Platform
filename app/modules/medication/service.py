"""
Medication Service Module

Handles business logic, pediatric safety rules, and permission checking for medication plans and dose administration logs.
"""
import logging
from datetime import datetime, timezone, date
from typing import Optional, List, Dict, Any
from app.modules.medication.schemas import (
    MedicationLogCreate,
    MedicationLogResponse,
    MedicationPlanCreate,
    MedicationPlanUpdate,
    MedicationPlanResponse,
    MedicationDoseLogCreate,
    MedicationDoseLogResponse,
    TodayDoseItem
)
from app.modules.medication.repository import (
    MedicationRepository,
    MedicationPlanRepository,
    MedicationDoseLogRepository
)
from app.modules.baby.service import BabyService
from app.modules.guardian.permissions import ADMIN, GUARDIAN, require_role
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


def _classify_session(time_str: str, frequency: str) -> str:
    """Phân loại buổi uống dựa trên mốc thời gian hoặc tần suất."""
    if "sốt" in frequency.lower() or "prn" in frequency.lower():
        return "prn"
    try:
        hour = int(time_str.split(":")[0])
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 21:
            return "evening"
        else:
            return "night"
    except Exception:
        return "morning"


class MedicationService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    # =========================================================================
    # 1. MEDICATION PLAN (Đơn thuốc / Phác đồ)
    # =========================================================================

    def create_medication_plan(self, baby_id: str, plan_in: MedicationPlanCreate, user_id: str) -> MedicationPlanResponse:
        """
        Tạo một đơn thuốc mới có cấu trúc sau khi kiểm tra quyền giám hộ.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        repo = MedicationPlanRepository(baby_id)

        now_iso = datetime.now(timezone.utc).isoformat()
        plan_obj = MedicationPlanResponse(
            baby_id=baby_id,
            name=plan_in.name.strip(),
            alternative_name=plan_in.alternative_name.strip() if plan_in.alternative_name else None,
            strength=plan_in.strength.strip() if plan_in.strength else None,
            dose=plan_in.dose.strip(),
            unit=plan_in.unit.strip(),
            route=plan_in.route,
            frequency=plan_in.frequency,
            schedule_times=plan_in.schedule_times or ["08:00"],
            meal_timing=plan_in.meal_timing,
            start_date=plan_in.start_date,
            end_date=plan_in.end_date,
            duration_days=plan_in.duration_days,
            purpose=plan_in.purpose,
            instructions=plan_in.instructions,
            prescribed_by=plan_in.prescribed_by or "Bác sĩ nhi khoa",
            status=plan_in.status or "active",
            created_at=now_iso,
            updated_at=now_iso
        )
        return repo.create(plan_obj)

    def get_medication_plans(self, baby_id: str, user_id: str, status_filter: Optional[str] = None) -> List[MedicationPlanResponse]:
        """
        Lấy danh sách tất cả các đơn thuốc của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = MedicationPlanRepository(baby_id)
        plans = repo.list(limit=500)
        if status_filter:
            plans = [p for p in plans if p.status == status_filter]
        plans.sort(key=lambda x: str(x.created_at or ""), reverse=True)
        return plans

    def get_medication_plan_by_id(self, baby_id: str, plan_id: str, user_id: str) -> MedicationPlanResponse:
        """
        Lấy chi tiết một đơn thuốc.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = MedicationPlanRepository(baby_id)
        plan = repo.get(plan_id)
        if not plan:
            raise EntityNotFoundError("Không tìm thấy đơn thuốc của bé")
        return plan

    def update_medication_plan(self, baby_id: str, plan_id: str, update_in: MedicationPlanUpdate, user_id: str) -> MedicationPlanResponse:
        """
        Cập nhật thông tin hoặc trạng thái đơn thuốc (active / completed / paused).
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        repo = MedicationPlanRepository(baby_id)
        existing = repo.get(plan_id)
        if not existing:
            raise EntityNotFoundError("Không tìm thấy đơn thuốc để cập nhật")

        update_data = {k: v for k, v in update_in.model_dump().items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        return repo.update(plan_id, update_data)

    def delete_medication_plan(self, baby_id: str, plan_id: str, user_id: str) -> bool:
        """
        Xóa một đơn thuốc của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        repo = MedicationPlanRepository(baby_id)
        existing = repo.get(plan_id)
        if not existing:
            raise EntityNotFoundError("Không tìm thấy đơn thuốc để xóa")
        return repo.delete(plan_id)

    # =========================================================================
    # 2. TODAY'S DOSE CHECKLIST (Checklist cữ thuốc hôm nay)
    # =========================================================================

    def get_today_doses(self, baby_id: str, user_id: str, target_date_str: Optional[str] = None) -> List[TodayDoseItem]:
        """
        Tính toán danh sách các cữ thuốc cần uống cho ngày hôm nay từ các đơn thuốc active,
        kèm trạng thái đã uống/chưa uống từ Dose Log.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        today_str = target_date_str or datetime.now().strftime("%Y-%m-%d")

        # 1. Lấy tất cả plans đang active
        plan_repo = MedicationPlanRepository(baby_id)
        active_plans = [p for p in plan_repo.list(limit=200) if p.status == "active"]

        # 2. Lấy logs của ngày hôm nay
        dose_repo = MedicationDoseLogRepository(baby_id)
        today_logs = [log for log in dose_repo.list(limit=500) if log.scheduled_date == today_str]

        # Ánh xạ dose logs theo key: plan_id + scheduled_time
        logged_map: Dict[str, MedicationDoseLogResponse] = {}
        for log in today_logs:
            key = f"{log.plan_id}_{log.scheduled_time}"
            logged_map[key] = log

        today_items: List[TodayDoseItem] = []

        for plan in active_plans:
            # Kiểm tra thời hạn hiệu lực của đơn thuốc
            if plan.start_date and today_str < plan.start_date:
                continue
            if plan.end_date and today_str > plan.end_date:
                continue

            for t_slot in (plan.schedule_times or ["08:00"]):
                slot_key = f"{plan.id}_{t_slot}"
                matched_log = logged_map.get(slot_key)

                status_val = "pending"
                taken_at_val = None
                admin_by_val = None

                if matched_log:
                    status_val = matched_log.status if matched_log.status in ["taken", "skipped"] else "pending"
                    taken_at_val = matched_log.taken_at
                    admin_by_val = matched_log.administered_by

                dose_display = f"{plan.dose} {plan.unit}"
                session_type = _classify_session(t_slot, plan.frequency)

                today_items.append(
                    TodayDoseItem(
                        dose_id=matched_log.id if matched_log and matched_log.id else f"dose_{plan.id}_{t_slot}",
                        plan_id=plan.id,
                        medication_name=plan.name,
                        alternative_name=plan.alternative_name,
                        strength=plan.strength,
                        dose_display=dose_display,
                        route=plan.route,
                        meal_timing=plan.meal_timing,
                        scheduled_time=t_slot,
                        session=session_type, # type: ignore
                        status=status_val, # type: ignore
                        taken_at=taken_at_val,
                        administered_by=admin_by_val,
                        instructions=plan.instructions,
                        purpose=plan.purpose
                    )
                )

        # Sắp xếp theo giờ uống
        today_items.sort(key=lambda x: x.scheduled_time)
        return today_items

    # =========================================================================
    # 3. LOG DOSE ADMINISTRATION (Ghi nhận cữ uống)
    # =========================================================================

    def log_dose_action(self, baby_id: str, log_in: MedicationDoseLogCreate, user_id: str) -> MedicationDoseLogResponse:
        """
        Ghi nhận phụ huynh đã cho bé uống thuốc hoặc bỏ qua cữ thuốc.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        dose_repo = MedicationDoseLogRepository(baby_id)

        now_iso = datetime.now(timezone.utc).isoformat()
        log_obj = MedicationDoseLogResponse(
            baby_id=baby_id,
            plan_id=log_in.plan_id,
            medication_name=log_in.medication_name,
            scheduled_date=log_in.scheduled_date,
            scheduled_time=log_in.scheduled_time,
            taken_at=log_in.taken_at or now_iso,
            dose_taken=log_in.dose_taken,
            status=log_in.status,
            administered_by=log_in.administered_by or "Phụ huynh",
            notes=log_in.notes,
            created_at=now_iso
        )
        created = dose_repo.create(log_obj)

        # Đồng thời tạo legacy MedicationLog để tương thích ngược với trang cũ
        try:
            legacy_repo = MedicationRepository(baby_id)
            legacy_repo.create(
                MedicationLogResponse(
                    medication_name=log_in.medication_name,
                    dosage=log_in.dose_taken,
                    logged_at=log_in.taken_at or now_iso,
                    prescribed_by=log_in.administered_by or "Phụ huynh",
                    notes=log_in.notes
                )
            )
        except Exception as e:
            logger.warning(f"Failed to sync legacy medication log: {e}")

        return created

    def get_dose_history(self, baby_id: str, user_id: str, limit: int = 200) -> List[MedicationDoseLogResponse]:
        """
        Lấy toàn bộ lịch sử cữ uống của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        dose_repo = MedicationDoseLogRepository(baby_id)
        logs = dose_repo.list(limit=limit)
        logs.sort(key=lambda x: str(x.taken_at or x.created_at or ""), reverse=True)
        return logs

    # =========================================================================
    # 4. BACKWARDS COMPATIBILITY METHODS
    # =========================================================================

    def add_medication_log(self, baby_id: str, log_in: MedicationLogCreate, user_id: str) -> MedicationLogResponse:
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
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
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = MedicationRepository(baby_id)
        logs = repo.list(limit=500)
        logs.sort(key=lambda x: str(x.logged_at or ""), reverse=True)
        return logs

    def delete_medication_log(self, baby_id: str, log_id: str, user_id: str) -> bool:
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        repo = MedicationRepository(baby_id)
        log = repo.get(log_id)
        if not log:
            raise EntityNotFoundError("Không tìm thấy bản ghi nhật ký dùng thuốc")
        return repo.delete(log_id)

