"""
Sleep Service Module
====================
Handles business logic and permission checking for baby sleep tracking and timers.
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List
from app.modules.sleep.schemas import SleepLogCreate, SleepLogResponse, SleepTimerResponse
from app.modules.sleep.repository import SleepRepository
from app.modules.baby.service import BabyService
from app.infrastructure.database.connection import get_firestore_db
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


class SleepService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    def add_sleep_log(self, baby_id: str, log_in: SleepLogCreate, user_id: str) -> SleepLogResponse:
        """
        Ghi nhận nhật ký giấc ngủ mới cho bé sau khi kiểm tra quyền giám hộ.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = SleepRepository(baby_id)

        now_iso = datetime.now(timezone.utc).isoformat()
        log_obj = SleepLogResponse(
            action=log_in.action,
            duration_minutes=log_in.duration_minutes,
            start_time=log_in.start_time,
            end_time=log_in.end_time,
            notes=log_in.notes,
            logged_at=log_in.logged_at or now_iso
        )
        return repo.create(log_obj)

    def get_sleep_history(self, baby_id: str, user_id: str, limit: int = 50) -> List[SleepLogResponse]:
        """
        Lấy lịch sử giấc ngủ của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = SleepRepository(baby_id)
        logs = repo.list(limit=limit)
        logs.sort(key=lambda x: x.logged_at, reverse=True)
        return logs

    def handle_sleep_timer(self, baby_id: str, action: str, user_id: str) -> SleepTimerResponse:
        """
        Quản lý bộ hẹn giờ giấc ngủ (Bắt đầu, Dừng, Kiểm tra trạng thái).
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        db = get_firestore_db()
        timer_ref = db.collection("sleep_timers").document(baby_id)
        doc = timer_ref.get()

        if action == "status":
            if not doc.exists or not doc.to_dict().get("is_running"):
                return SleepTimerResponse(baby_id=baby_id, is_running=False, message="Timer không chạy")
            data = doc.to_dict()
            started_at = data.get("started_at")
            start_dt = datetime.fromisoformat(started_at)
            now_dt = datetime.now(timezone.utc)
            elapsed = int((now_dt - start_dt).total_seconds())
            return SleepTimerResponse(
                baby_id=baby_id,
                is_running=True,
                started_at=started_at,
                elapsed_seconds=elapsed,
                message=f"Bé đang ngủ được {elapsed // 60} phút"
            )

        elif action == "start":
            now_iso = datetime.now(timezone.utc).isoformat()
            timer_ref.set({"is_running": True, "started_at": now_iso})
            # Ghi nhận trạng thái bắt đầu vào nhật ký giấc ngủ
            self.add_sleep_log(baby_id, SleepLogCreate(action="start_sleep", start_time=now_iso), user_id)
            return SleepTimerResponse(
                baby_id=baby_id,
                is_running=True,
                started_at=now_iso,
                elapsed_seconds=0,
                message="Đã bắt đầu hẹn giờ giấc ngủ cho bé"
            )

        elif action == "stop":
            if not doc.exists or not doc.to_dict().get("is_running"):
                return SleepTimerResponse(baby_id=baby_id, is_running=False, message="Timer chưa được bật")
            data = doc.to_dict()
            started_at = data.get("started_at")
            start_dt = datetime.fromisoformat(started_at)
            now_dt = datetime.now(timezone.utc)
            elapsed_minutes = max(1, int((now_dt - start_dt).total_seconds() / 60))
            
            timer_ref.delete()
            # Ghi nhận hoàn thành giấc ngủ
            self.add_sleep_log(
                baby_id,
                SleepLogCreate(action="wake", duration_minutes=elapsed_minutes, start_time=started_at, end_time=now_dt.isoformat()),
                user_id
            )
            return SleepTimerResponse(
                baby_id=baby_id,
                is_running=False,
                started_at=None,
                elapsed_seconds=0,
                message=f"Đã kết thúc giấc ngủ ({elapsed_minutes} phút) và lưu vào nhật ký"
            )
        else:
            raise ValueError(f"Hành động timer không hợp lệ: {action}")

    async def predict_next_wake_window(
        self, 
        baby_id: str, 
        user_id: str, 
        current_time: Optional[datetime] = None
    ):
        """
        Dự đoán Wake Window và Giấc ngủ tiếp theo của bé bám sát Patent US 20250292903:
        1. Lấy thông tin bé (ngày sinh) & quyền giám hộ.
        2. Lấy 50 logs gần nhất từ SleepRepository.
        3. Chạy Per-Baby Feature Engineering (trích xuất chuỗi 5 ngày gần nhất).
        4. Chạy Global LightGBM + Safety Guardrails + LLM Anomaly Reasoner.
        """
        from app.modules.sleep.feature_engineering import FeatureEngineeringEngine
        from app.modules.sleep.wake_window_predictor import WakeWindowPredictionService

        # 1. Kiểm tra quyền giám hộ và lấy thông tin ngày sinh
        baby = self.baby_service.get_baby_by_id(baby_id, user_id)
        birthday_str = baby.birth_date if hasattr(baby, "birth_date") else None

        # 2. Lấy lịch sử giấc ngủ gần nhất
        logs = self.get_sleep_history(baby_id, user_id, limit=50)

        # 3. Lấy nhật ký sức khỏe gần nhất nếu có
        health_logs = []
        try:
            db = get_firestore_db()
            health_docs = db.collection(f"babies/{baby_id}/health_records").limit(10).stream()
            for doc in health_docs:
                d = doc.to_dict()
                d["id"] = doc.id
                health_logs.append(d)
        except Exception:
            health_logs = []

        # 4. Trích xuất vector đặc trưng bám sát Patent US 20250292903
        features = FeatureEngineeringEngine.extract_features_from_logs(
            baby_id=baby_id,
            birthday_str=birthday_str,
            sleep_logs=logs,
            current_time=current_time,
        )

        # 5. Thực hiện dự đoán
        return await WakeWindowPredictionService.predict_next_wake_window(
            baby_id=baby_id,
            features=features,
            health_logs=health_logs,
            current_time=current_time,
        )

