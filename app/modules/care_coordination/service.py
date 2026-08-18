"""
Care Coordination Service - Xử lý nghiệp vụ điều phối chăm sóc, kiểm tra quyền và đồng bộ dữ liệu.
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timezone

from app.modules.care_coordination.schemas import (
    HandoverNoteCreate,
    HandoverNoteResponse,
    CareTaskCreate,
    CareTaskUpdate,
    CareTaskCompleteRequest,
    CareTaskResponse,
    CareEventCreate,
    CareEventResponse,
    CareTimelineSummary,
    WorkloadStatsResponse,
    CaregiverWorkloadItem,
    TaskStatusEnum,
    TaskTypeEnum
)
from app.modules.care_coordination.repository import CareCoordinationRepository
from app.modules.baby.service import BabyService
from app.shared.exceptions import EntityNotFoundError, PermissionDeniedError

logger = logging.getLogger(__name__)


class CareCoordinationService:
    def __init__(
        self,
        repo: Optional[CareCoordinationRepository] = None,
        baby_service: Optional[BabyService] = None
    ):
        self.repo = repo or CareCoordinationRepository()
        self.baby_service = baby_service or BabyService()

    # ─── 1. HANDOVER NOTES ───────────────────────────────────────────────────

    def get_today_handover(self, baby_id: str, user_id: str, date_str: Optional[str] = None) -> Optional[HandoverNoteResponse]:
        """Lấy lời dặn bàn giao trong ngày của bé."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        target_date = date_str or date.today().isoformat()
        
        doc = self.repo.get_handover_by_date(baby_id, target_date)
        if not doc:
            return None
        return HandoverNoteResponse(**doc)

    def save_handover_note(
        self,
        note_in: HandoverNoteCreate,
        user_id: str,
        author_name: str = "Phụ huynh"
    ) -> HandoverNoteResponse:
        """Tạo hoặc cập nhật lời dặn bàn giao buổi sáng."""
        self.baby_service.get_baby_by_id(note_in.baby_id, user_id)
        target_date = note_in.date or date.today().isoformat()

        payload = {
            "baby_id": note_in.baby_id,
            "date": target_date,
            "created_by": user_id,
            "author_name": author_name,
            "content": note_in.content,
            "voice_note_url": note_in.voice_note_url,
            "photo_urls": note_in.photo_urls or [],
            "acknowledged_by": []
        }
        doc_id = self.repo.create_or_update_handover(payload)
        doc = self.repo.get_handover_by_date(note_in.baby_id, target_date)
        return HandoverNoteResponse(**doc)

    # ─── 2. CARE TASKS ───────────────────────────────────────────────────────

    def get_today_tasks(self, baby_id: str, user_id: str, date_str: Optional[str] = None) -> List[CareTaskResponse]:
        """Lấy danh sách các việc cần làm trong ngày của bé."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        target_date = date_str or date.today().isoformat()

        raw_tasks = self.repo.list_tasks_by_date(baby_id, target_date)
        return [CareTaskResponse(**t) for t in raw_tasks]

    def create_care_task(
        self,
        task_in: CareTaskCreate,
        user_id: str
    ) -> CareTaskResponse:
        """Tạo một việc cần làm mới cho bé."""
        self.baby_service.get_baby_by_id(task_in.baby_id, user_id)
        
        # Đảm bảo scheduled_time có định dạng chuẩn
        scheduled = task_in.scheduled_time
        if len(scheduled) <= 5 and ":" in scheduled:
            # Nếu người dùng chỉ truyền "14:30" -> Ghép ngày hôm nay vào
            today_str = date.today().isoformat()
            scheduled = f"{today_str}T{scheduled}:00Z"

        payload = {
            "baby_id": task_in.baby_id,
            "task_type": task_in.task_type.value,
            "title": task_in.title,
            "scheduled_time": scheduled,
            "assigned_to": task_in.assigned_to,
            "assigned_name": task_in.assigned_name or "Người chăm sóc",
            "instructions": task_in.instructions or "",
            "target_value": task_in.target_value or {},
            "status": TaskStatusEnum.PENDING.value,
            "priority": task_in.priority.value,
            "is_recurring": task_in.is_recurring,
            "created_by": user_id
        }
        doc_id = self.repo.create_task(payload)
        doc = self.repo.get_task_by_id(doc_id)
        return CareTaskResponse(**doc)

    def complete_task(
        self,
        task_id: str,
        complete_in: CareTaskCompleteRequest,
        user_id: str,
        user_name: str = "Người chăm sóc"
    ) -> CareTaskResponse:
        """
        Người chăm sóc tick 1-chạm hoàn thành task và ghi nhận giá trị thực tế.
        Tự động tạo CareEvent và đồng bộ dữ liệu sang Nutrition / Health Records.
        """
        task_doc = self.repo.get_task_by_id(task_id)
        if not task_doc:
            raise EntityNotFoundError(f"Không tìm thấy việc cần làm mã: {task_id}")

        baby_id = task_doc["baby_id"]
        self.baby_service.get_baby_by_id(baby_id, user_id)

        now_utc = datetime.now(timezone.utc).isoformat()
        occurred_at = complete_in.occurred_at or now_utc
        actual_val = complete_in.actual_value or task_doc.get("target_value", {})

        # 1. Cập nhật trạng thái Task
        updates = {
            "status": TaskStatusEnum.COMPLETED.value,
            "completed_at": now_utc,
            "completed_by": user_id,
            "actual_value": actual_val,
            "completion_notes": complete_in.notes or ""
        }
        self.repo.update_task(task_id, updates)

        # 2. Tạo bản ghi CareEvent (Thực tế đã diễn ra)
        event_payload = {
            "baby_id": baby_id,
            "task_id": task_id,
            "event_type": task_doc.get("task_type", "custom"),
            "occurred_at": occurred_at,
            "recorded_by": user_id,
            "recorded_by_name": complete_in.completed_by_name or user_name,
            "actual_value": actual_val,
            "notes": complete_in.notes or ""
        }
        
        # 3. Đồng bộ 2 chiều sang các Module chuyên sâu
        self._auto_sync_to_modules(event_payload, user_id)
        
        self.repo.create_event(event_payload)
        
        updated_doc = self.repo.get_task_by_id(task_id)
        return CareTaskResponse(**updated_doc)

    def delete_task(self, task_id: str, user_id: str) -> bool:
        """Xóa một task."""
        task_doc = self.repo.get_task_by_id(task_id)
        if not task_doc:
            raise EntityNotFoundError(f"Không tìm thấy việc cần làm mã: {task_id}")
        
        self.baby_service.get_baby_by_id(task_doc["baby_id"], user_id)
        return self.repo.delete_task(task_id)

    # ─── 3. TIMELINE & SUMMARY ───────────────────────────────────────────────

    def check_and_update_overdue_tasks(self, baby_id: str, user_id: str, date_str: Optional[str] = None) -> List[CareTaskResponse]:
        """
        Quét các task trong ngày: nếu quá hạn > 30 phút mà chưa hoàn thành -> chuyển sang trạng thái OVERDUE.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        target_date = date_str or date.today().isoformat()
        raw_tasks = self.repo.list_tasks_by_date(baby_id, target_date)
        now_dt = datetime.now(timezone.utc)
        overdue_updated = []

        for t in raw_tasks:
            if t.get("status") == TaskStatusEnum.PENDING.value:
                sched_str = t.get("scheduled_time", "")
                try:
                    if "T" in sched_str:
                        sched_dt = datetime.fromisoformat(sched_str.replace("Z", "+00:00"))
                    else:
                        # Ghép ngày
                        sched_dt = datetime.fromisoformat(f"{target_date}T{sched_str}:00+00:00")
                    
                    # Nếu thời gian hiện tại đã vượt quá thời gian lên lịch 30 phút
                    if (now_dt - sched_dt).total_seconds() > 1800:
                        self.repo.update_task(t["id"], {"status": TaskStatusEnum.OVERDUE.value})
                        t["status"] = TaskStatusEnum.OVERDUE.value
                        overdue_updated.append(CareTaskResponse(**t))
                except Exception:
                    pass

        return overdue_updated

    def get_timeline_summary(self, baby_id: str, user_id: str, date_str: Optional[str] = None) -> CareTimelineSummary:
        """Tổng hợp toàn bộ bức tranh chăm sóc trong ngày: Lời dặn, Tasks, Events và Cảnh báo ngoại lệ."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        target_date = date_str or date.today().isoformat()

        # Tự động quét cập nhật task quá hạn
        self.check_and_update_overdue_tasks(baby_id, user_id, target_date)

        handover = self.get_today_handover(baby_id, user_id, target_date)
        tasks = self.get_today_tasks(baby_id, user_id, target_date)
        raw_events = self.repo.list_events_by_date(baby_id, target_date)
        events = [CareEventResponse(**e) for e in raw_events]

        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatusEnum.COMPLETED.value)
        overdue = sum(1 for t in tasks if t.status == TaskStatusEnum.OVERDUE.value)

        # AI summary text thân thiện, ấm áp
        ai_summary = ""
        if overdue > 0:
            ai_summary = f"⚠️ Cảnh báo: Hiện có {overdue} cữ chăm sóc quá giờ quy định chưa được xác nhận hoàn thành. Bố mẹ nên kiểm tra lại với người ở nhà nhé!"
        elif total > 0:
            ai_summary = f"Hôm nay bé đã hoàn thành {completed}/{total} cữ chăm sóc theo kế hoạch."
            if completed == total:
                ai_summary += " 🎉 Tuyệt vời! Tất cả các cữ chăm sóc hôm nay đã được thực hiện đầy đủ và đúng chuẩn."
        else:
            ai_summary = "Chưa có lịch trình được tạo cho ngày hôm nay. Bố mẹ có thể tạo lịch dặn dò để người ở nhà dễ dàng theo dõi nhé."

        return CareTimelineSummary(
            baby_id=baby_id,
            date=target_date,
            total_tasks=total,
            completed_tasks=completed,
            overdue_tasks=overdue,
            handover_note=handover,
            tasks=tasks,
            recent_events=events,
            ai_summary_text=ai_summary
        )

    # ─── 4. DYNAMIC ESCALATION ───────────────────────────────────────────────

    def escalate_task(
        self,
        task_id: str,
        user_id: str,
        new_assignee_id: Optional[str] = None,
        new_assignee_name: Optional[str] = None,
        reason: str = "Tự động chuyển giao do quá hạn thực hiện"
    ) -> CareTaskResponse:
        """
        Chuyển giao việc khẩn cấp cho người dự phòng (Dynamic Escalation) khi người chính không thực hiện.
        """
        task_doc = self.repo.get_task_by_id(task_id)
        if not task_doc:
            raise EntityNotFoundError(f"Không tìm thấy việc cần làm mã: {task_id}")

        self.baby_service.get_baby_by_id(task_doc["baby_id"], user_id)
        now_utc = datetime.now(timezone.utc).isoformat()

        target_assignee = new_assignee_name or task_doc.get("backup_assigned_name") or "Bố/Mẹ (Người dự phòng)"
        target_id = new_assignee_id or task_doc.get("backup_assigned_to") or user_id

        updates = {
            "status": TaskStatusEnum.ESCALATED.value,
            "assigned_to": target_id,
            "assigned_name": target_assignee,
            "escalated_at": now_utc,
            "escalation_reason": reason
        }
        self.repo.update_task(task_id, updates)
        updated_doc = self.repo.get_task_by_id(task_id)
        return CareTaskResponse(**updated_doc)

    # ─── 5. WORKLOAD ANALYTICS ───────────────────────────────────────────────

    def get_workload_analytics(self, baby_id: str, user_id: str, period_days: int = 7) -> WorkloadStatsResponse:
        """
        Tính toán phân bổ khối lượng công việc chăm sóc giữa các thành viên trong gia đình (Workload Balance).
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        
        from datetime import timedelta
        end_date = date.today()
        start_date = end_date - timedelta(days=period_days - 1)

        # Gom toàn bộ tasks trong kỳ
        all_tasks = []
        curr = start_date
        while curr <= end_date:
            daily_tasks = self.repo.list_tasks_by_date(baby_id, curr.isoformat())
            all_tasks.extend(daily_tasks)
            curr += timedelta(days=1)

        total_assigned = len(all_tasks)
        total_completed = sum(1 for t in all_tasks if t.get("status") == TaskStatusEnum.COMPLETED.value)

        # Thống kê theo từng người chăm sóc
        caregiver_stats: Dict[str, Dict[str, int]] = {}
        for t in all_tasks:
            name = t.get("assigned_name") or "Người chăm sóc"
            if name not in caregiver_stats:
                caregiver_stats[name] = {"assigned": 0, "completed": 0}
            caregiver_stats[name]["assigned"] += 1
            if t.get("status") == TaskStatusEnum.COMPLETED.value:
                caregiver_stats[name]["completed"] += 1

        distribution = []
        top_caregiver = None
        top_percentage = 0.0

        for name, stats in caregiver_stats.items():
            pct = round((stats["assigned"] / total_assigned) * 100, 1) if total_assigned > 0 else 0.0
            rate = round((stats["completed"] / stats["assigned"]) * 100, 1) if stats["assigned"] > 0 else 0.0
            distribution.append(CaregiverWorkloadItem(
                caregiver_name=name,
                assigned_tasks_count=stats["assigned"],
                completed_tasks_count=stats["completed"],
                workload_percentage=pct,
                completion_rate=rate
            ))
            if pct > top_percentage:
                top_percentage = pct
                top_caregiver = name

        # AI Cân bằng khối lượng công việc khuyến nghị
        rebalance_text = None
        if total_assigned >= 5 and top_percentage >= 60.0 and top_caregiver:
            rebalance_text = (
                f"💡 Gợi ý điều phối: {top_caregiver} đang phụ trách {top_percentage}% khối lượng công việc "
                f"trong {period_days} ngày qua. Gia đình có thể phân bổ bớt 1-2 cữ buổi tối cho thành viên khác để giảm áp lực nhé!"
            )
        elif total_assigned > 0:
            rebalance_text = "✨ Khối lượng công việc chăm sóc đang được phân bổ khá cân bằng giữa các thành viên trong gia đình."

        return WorkloadStatsResponse(
            baby_id=baby_id,
            period_days=period_days,
            total_tasks_assigned=total_assigned,
            total_tasks_completed=total_completed,
            caregivers_distribution=distribution,
            ai_rebalance_recommendation=rebalance_text
        )

    # ─── 4. HELPER SYNC FUNCTIONS ────────────────────────────────────────────

    def _auto_sync_to_modules(self, event_data: dict, user_id: str) -> None:
        """Đồng bộ tự động CareEvent sang Nutrition hoặc Health Records."""
        event_type = event_data.get("event_type")
        baby_id = event_data.get("baby_id")
        actual_val = event_data.get("actual_value", {})
        notes = event_data.get("notes", "")

        try:
            if event_type == TaskTypeEnum.FEEDING.value:
                # Đồng bộ sang Nutrition Log
                from app.modules.nutrition.repository import SolidFoodRepository
                from app.modules.nutrition.schemas import SolidFoodLogResponse
                
                amount = actual_val.get("amount", actual_val.get("volume_ml", 0))
                food_name = actual_val.get("food_name", "Sữa")
                
                repo = SolidFoodRepository(baby_id)
                log_obj = SolidFoodLogResponse(
                    logged_at=event_data.get("occurred_at"),
                    food_name=food_name,
                    amount_g=int(amount),
                    reaction="Ngoan",
                    notes=notes or f"Ghi nhận từ lịch chăm sóc bởi {event_data.get('recorded_by_name')}"
                )
                repo.create(log_obj)
                event_data["synced_to_module"] = "nutrition"
                logger.info(f"[CareCoordination] Auto-synced feeding event to nutrition logs for baby {baby_id}")

            elif event_type == TaskTypeEnum.MEDICATION.value:
                # Đồng bộ sang Health Records
                from app.modules.health_records.repository import HealthRecordRepository
                
                med_name = actual_val.get("medication_name", "Thuốc")
                dosage = str(actual_val.get("dosage", "1 liều"))
                
                repo = HealthRecordRepository(baby_id)
                repo.create({
                    "baby_id": baby_id,
                    "recorded_at": event_data.get("occurred_at"),
                    "diagnosis": f"Uống {med_name} ({dosage})",
                    "doctor_notes": notes or f"Đã cho bé uống bởi {event_data.get('recorded_by_name')}",
                    "created_at": datetime.now(timezone.utc).isoformat()
                })
                event_data["synced_to_module"] = "health_records"
                logger.info(f"[CareCoordination] Auto-synced medication event to health records for baby {baby_id}")

        except Exception as e:
            logger.warning(f"[CareCoordination] Auto-sync to module failed (non-critical): {e}")
