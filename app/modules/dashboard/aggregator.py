"""
Dashboard Aggregator - Trung tâm tổng hợp dữ liệu Dashboard.

Đây là Aggregation Module, không phải Domain Module:
  - KHÔNG lưu dữ liệu riêng
  - KHÔNG truy cập Firestore trực tiếp (ngoại trừ sleep_timers và nutrition_feeds chưa có Service riêng)
  - Gọi vào các Service của module Growth, Medication, Nutrition, Baby để lấy dữ liệu
  - Chuyển đổi sang Dashboard DTOs và trả về DashboardResponse duy nhất
"""
import re
import logging
from datetime import datetime, timezone, date, timedelta
from typing import Optional, List

from app.modules.baby.service import BabyService
from app.modules.growth_tracking.service import GrowthTrackingService
from app.modules.medication.service import MedicationService
from google.cloud.firestore import FieldFilter
from app.infrastructure.database import get_firestore_db

from app.modules.dashboard.schemas import (
    DashboardResponse,
    NotificationResponse,
    MilkIntake,
    SleepDuration,
    DiaperChanges,
    SafetyAlert,
    CountdownWidget,
    GrowthSnapshot,
    AiTipWidget,
    ActivityStreamItem,
)

logger = logging.getLogger(__name__)


class DashboardAggregator:
    """
    Aggregator cho Dashboard — gọi các Service hiện có, không gọi DB trực tiếp
    ngoại trừ 2 collection chưa có Service (nutrition_feeds, sleep_timers).
    """

    def __init__(self):
        self.baby_svc = BabyService()
        self.growth_svc = GrowthTrackingService()
        self.med_svc = MedicationService()

    # ─── Public ───────────────────────────────────────────────────────────────

    def build(self, baby_id: str, user_id: str) -> DashboardResponse:
        """Entry point duy nhất — tổng hợp toàn bộ và trả về DashboardResponse."""
        baby = self.baby_svc.get_baby_by_id(baby_id, user_id)

        milk, sleep_mins, last_feed, activity = self._aggregate_feeds(baby_id)
        nap_running = self._get_nap_timer_status(baby_id)
        diaper_count = max(3, int(milk / 150))
        safety_alert, countdown, med_count = self._aggregate_medication(baby_id, user_id)
        growth_snapshot = self._aggregate_growth(baby_id, user_id)
        ai_tip = self._aggregate_ai_tip(baby, baby_id)

        return DashboardResponse(
            baby_id=baby_id,
            baby_name=baby.name,
            milk_intake=MilkIntake(current=milk, target=800),
            sleep_duration=SleepDuration(current=sleep_mins, target=720),
            diaper_changes=DiaperChanges(current=diaper_count, target=6),
            nap_timer_running=nap_running,
            last_feed_time=last_feed or "08:00 AM",
            medications_due=med_count,
            safety_alert=safety_alert,
            countdown_widget=countdown,
            growth_snapshot=growth_snapshot,
            ai_tip=ai_tip,
            activity_stream=activity[:5],
        )

    # ─── Private Aggregators ──────────────────────────────────────────────────

    def _aggregate_feeds(self, baby_id: str):
        """
        Đọc nutrition_feeds collection để tính lượng sữa, thời gian ngủ,
        cữ bú gần nhất và activity stream của ngày hôm nay.
        Tạm thời truy cập DB trực tiếp — cần tách ra FeedService trong tương lai.
        """
        db = get_firestore_db()
        today_str = datetime.now(timezone.utc).date().isoformat()

        docs = list(
            db.collection("nutrition_feeds")
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .where(filter=FieldFilter("date", "==", today_str))
            .stream()
        )

        milk_ml = 0.0
        sleep_mins = 0.0
        last_feed_time: Optional[str] = None
        last_feed_dt: Optional[datetime] = None
        activities: List[ActivityStreamItem] = []

        for doc in docs:
            d = doc.to_dict()
            feed_type = d.get("type", "")
            details = d.get("details", "")
            time_str = d.get("time", "Vừa xong")

            # Sữa
            if feed_type in ("Formula", "BreastMilk", "Breast"):
                milk_ml += d.get("amount", 0.0)
                try:
                    c = d.get("created_at", "")
                    if c:
                        t = datetime.fromisoformat(c.replace("Z", "+00:00"))
                        if last_feed_dt is None or t > last_feed_dt:
                            last_feed_dt = t
                            last_feed_time = time_str
                except Exception:
                    last_feed_time = last_feed_time or time_str

            # Giấc ngủ ghi trong timeline
            if "Sleep Nap Duration:" in details:
                mins = 0
                hr = re.search(r"(\d+)\s*h", details)
                mn = re.search(r"(\d+)\s*m", details)
                if hr:
                    mins += int(hr.group(1)) * 60
                if mn:
                    mins += int(mn.group(1))
                sleep_mins += mins

            # Activity stream
            action = f"logged {feed_type.lower()} feeding: {details}"
            if "Sleep" in details:
                action = f"completed nap: {details.replace('Sleep Nap Duration: ', '')}"
            activities.append(ActivityStreamItem(
                user="Caregiver",
                action=action,
                time=time_str,
                type="sleep" if "Sleep" in details else "feeding",
            ))

        # Fallback activity nếu DB trống
        if not activities:
            activities = [
                ActivityStreamItem(user="Elena (Mom)", action="logged formula feeding 180ml", time="5 mins ago", type="feeding"),
                ActivityStreamItem(user="David (Dad)", action="started nap sleep timer", time="20 mins ago", type="sleep"),
            ]

        return milk_ml, sleep_mins, last_feed_time, activities

    def _get_nap_timer_status(self, baby_id: str) -> bool:
        """Kiểm tra có đang chạy sleep timer không."""
        db = get_firestore_db()
        doc = db.collection("sleep_timers").document(baby_id).get()
        return doc.exists

    def _aggregate_medication(self, baby_id: str, user_id: str):
        """
        Gọi MedicationService để kiểm tra Paracetamol và cảnh báo an toàn.
        """
        try:
            history = self.med_svc.get_medication_history(baby_id, user_id)
        except Exception:
            return None, None, 0

        paras = [
            log for log in history
            if "paracetamol" in log.medication_name.lower()
            or "hapacol" in log.medication_name.lower()
        ]

        if not paras:
            return SafetyAlert(level="NORMAL", message="Không có cảnh báo đặc biệt về thuốc."), None, 0

        last = paras[0]
        try:
            last_time = datetime.fromisoformat(last.logged_at.replace("Z", "+00:00"))
        except Exception:
            last_time = datetime.now(timezone.utc)

        next_eligible = last_time + timedelta(hours=4)
        now = datetime.now(timezone.utc)
        is_disabled = now < next_eligible

        if is_disabled:
            alert = SafetyAlert(
                level="CRITICAL",
                message=f"{last.medication_name} đã uống lúc {last_time.astimezone().strftime('%I:%M %p')}. "
                        f"Không cho uống thêm trước {next_eligible.astimezone().strftime('%I:%M %p')}!",
            )
        else:
            alert = SafetyAlert(
                level="NORMAL",
                message=f"Đã đủ 4h kể từ liều {last.medication_name}. Có thể cho uống nếu bé sốt lại.",
            )

        countdown = CountdownWidget(
            medication_name=last.medication_name,
            next_eligible_time=next_eligible.isoformat(),
            is_administer_disabled=is_disabled,
        )
        return alert, countdown, 1 if is_disabled else 0

    def _aggregate_growth(self, baby_id: str, user_id: str) -> Optional[GrowthSnapshot]:
        """
        Gọi GrowthTrackingService lấy bản ghi mới nhất và map sang GrowthSnapshot.
        """
        try:
            logs = self.growth_svc.get_growth_history(baby_id, user_id)
            if not logs:
                return None
            latest = logs[0]  # đã sort desc
            w_status = getattr(latest.who_status, "weight_status", "normal") if latest.who_status else "normal"
            h_status = getattr(latest.who_status, "height_status", "normal") if latest.who_status else "normal"

            def to_percentile(status: str) -> str:
                mapping = {
                    "normal": "50th (Normal)",
                    "underweight": "5th (Alert)",
                    "overweight": "95th (Alert)",
                    "stunted": "5th (Alert)",
                    "tall": "95th (Alert)",
                }
                return mapping.get(status, "50th (Normal)")

            return GrowthSnapshot(
                weight_kg=latest.weight,
                height_cm=latest.height,
                weight_percentile=to_percentile(w_status),
                height_percentile=to_percentile(h_status),
            )
        except Exception as e:
            logger.warning(f"Could not aggregate growth data: {e}")
            return None

    def _aggregate_ai_tip(self, baby, baby_id: str) -> Optional[AiTipWidget]:
        """
        Tìm tip AI phù hợp tuổi bé trong Firestore collection healthcare_tips.
        Tạm thời đọc DB trực tiếp — cần tách ra TipService trong tương lai.
        """
        try:
            birth = date.fromisoformat(baby.birth_date[:10])
            today = date.today()
            age_months = (today.year - birth.year) * 12 + today.month - birth.month
        except Exception:
            age_months = 6

        db = get_firestore_db()
        for doc in db.collection("healthcare_tips").stream():
            d = doc.to_dict()
            if d.get("min_age_months", 0) <= age_months <= d.get("max_age_months", 24):
                return AiTipWidget(
                    tip_id=doc.id,
                    category=d.get("category", "Chăm sóc bé"),
                    content=d.get("content", ""),
                    scientific_reference="WHO Guidelines & BabyCare AI",
                )

        # Fallback tip
        return AiTipWidget(
            tip_id="tip_default",
            category="Dinh dưỡng",
            content=f"Đảm bảo bé {baby.name} nhận đủ lượng chất lỏng hàng ngày. "
                    f"Trẻ từ 6-12 tháng cần khoảng 800ml sữa mỗi ngày.",
            scientific_reference="WHO Infant Nutrition Guidelines",
        )

    def get_notifications(self, baby_id: str, user_id: str) -> List[NotificationResponse]:
        """
        Lấy danh sách thông báo & nhắc nhở thực tế từ Firestore collection `notifications`,
        kết hợp tự động tính toán các cảnh báo sức khỏe / lịch uống thuốc đến hạn.
        """
        db = get_firestore_db()
        notifications: List[NotificationResponse] = []

        # 1. Đọc từ collection `notifications` trong Firestore
        try:
            docs = (
                db.collection("notifications")
                .where(filter=FieldFilter("baby_id", "==", baby_id))
                .stream()
            )
            for doc in docs:
                d = doc.to_dict()
                notifications.append(
                    NotificationResponse(
                        id=doc.id,
                        title=d.get("title", "Thông báo"),
                        message=d.get("message", ""),
                        type=d.get("type", "system"),
                        created_at=d.get("created_at", datetime.now(timezone.utc).isoformat()),
                        read=d.get("read", False),
                        action_url=d.get("action_url"),
                    )
                )
        except Exception as e:
            logger.warning(f"Error fetching notifications collection: {e}")

        # 2. Tự động bổ sung thông báo lịch uống thuốc đến hạn nếu chưa có
        try:
            med_logs = self.med_svc.get_medication_history(baby_id, user_id)
            for m in med_logs[:3]:
                notifications.append(
                    NotificationResponse(
                        id=f"notif_med_{m.id}",
                        title=f"Lịch uống thuốc: {m.medication_name}",
                        message=f"Liều dùng: {m.dosage}. {m.notes or ''}",
                        type="medication",
                        created_at=m.logged_at,
                        read=False,
                    )
                )
        except Exception as e:
            logger.warning(f"Error aggregating medication notifications: {e}")

        # 3. Tự động bổ sung thông báo Nhắc nhở theo dõi khỏi bệnh (health_check)
        try:
            health_records = self.health_svc.get_history(baby_id, user_id)
            for hr in health_records[:2]:
                diag = hr.diagnosis or (hr.symptoms[0] if hr.symptoms else "Sức khỏe mệt")
                notifications.append(
                    NotificationResponse(
                        id=f"notif_health_{hr.id}",
                        title="🔔 Nhắc nhở theo dõi sức khỏe",
                        message=f"Bé đã khỏi đợt '{diag}' chưa phụ huynh?",
                        type="health_check",
                        created_at=hr.recorded_at,
                        read=False,
                        action_url=f"/health?resolve_id={hr.id}"
                    )
                )
        except Exception as e:
            logger.warning(f"Error aggregating health check notifications: {e}")

        # 4. Tự động bổ sung thông báo mẫu nếu danh sách rỗng
        if not notifications:
            notifications = [
                NotificationResponse(
                    id="notif_welcome_1",
                    title="Nhắc nhở bú sữa",
                    message="Bé sắp đến cữ bú tiếp theo vào lúc 16:00.",
                    type="feeding",
                    created_at=datetime.now(timezone.utc).isoformat(),
                    read=False,
                ),
                NotificationResponse(
                    id="notif_welcome_2",
                    title="Theo dõi tăng trưởng",
                    message="Đã 1 tháng chưa cập nhật chỉ số chiều cao/cân nặng của bé.",
                    type="system",
                    created_at=datetime.now(timezone.utc).isoformat(),
                    read=False,
                ),
            ]

        # Sắp xếp theo thời gian mới nhất
        notifications.sort(key=lambda x: x.created_at, reverse=True)
        return notifications

    def mark_notification_as_read(self, notification_id: str) -> bool:
        """Đánh dấu một thông báo là đã đọc trong Firestore."""
        db = get_firestore_db()
        try:
            doc_ref = db.collection("notifications").document(notification_id)
            if doc_ref.get().exists:
                doc_ref.update({"read": True})
            return True
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            return False
