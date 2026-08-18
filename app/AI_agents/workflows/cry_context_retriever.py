"""
Cry Context Retriever Module
============================
Truy xuất đa nguồn ngữ cảnh sinh hoạt & sức khỏe của bé phục vụ phân tích tiếng khóc:
1. Feeding (Ăn dặm, cữ bú, lượng ăn, thời gian cách cữ ăn)
2. Sleep (Cữ ngủ gần nhất, thời gian thức wake window)
3. Health (Thân nhiệt, triệu chứng sốt/nôn/ho, bệnh án gần đây)
4. Medication (Thuốc hạ sốt/kháng sinh đã uống gần nhất)
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from dateutil import parser as date_parser

from app.modules.cry.schemas import (
    CryContextBundle,
    FeedingContext,
    SleepContext,
    HealthContext,
    MedicationContext
)
from app.modules.nutrition.service import SolidFoodService
from app.modules.health_records.service import HealthRecordService
from app.modules.medication.service import MedicationService
from app.infrastructure.database.connection import get_firestore_db

logger = logging.getLogger(__name__)


class CryContextRetriever:
    """
    Thu thập và chuẩn hóa dữ liệu ngữ cảnh từ nhiều nguồn độc lập.
    Đảm bảo tính chịu lỗi (Fault-Tolerant): Nếu một service lỗi, các context còn lại vẫn hoạt động bình thường.
    """

    def __init__(
        self,
        nutrition_service: Optional[SolidFoodService] = None,
        health_service: Optional[HealthRecordService] = None,
        medication_service: Optional[MedicationService] = None
    ):
        self.nutrition_service = nutrition_service or SolidFoodService()
        self.health_service = health_service or HealthRecordService()
        self.medication_service = medication_service or MedicationService()

    @staticmethod
    def _calculate_minutes_diff(past_time_str: Optional[str], now: Optional[datetime] = None) -> Optional[int]:
        """Tính số phút chênh lệch giữa mốc thời gian quá khứ và hiện tại."""
        if not past_time_str:
            return None
        try:
            if now is None:
                now = datetime.now(timezone.utc)
            
            past_dt = date_parser.parse(past_time_str)
            if past_dt.tzinfo is None:
                past_dt = past_dt.replace(tzinfo=timezone.utc)
            
            diff_seconds = (now - past_dt).total_seconds()
            return max(0, int(diff_seconds / 60))
        except Exception:
            return None

    def retrieve_feeding(self, baby_id: str, user_id: str, now: Optional[datetime] = None) -> FeedingContext:
        """Truy xuất nhật ký cữ ăn / ăn dặm gần nhất."""
        try:
            logs = self.nutrition_service.get_solid_food_history(baby_id, user_id)
            if logs:
                latest = logs[0]
                mins_ago = self._calculate_minutes_diff(latest.logged_at, now)
                return FeedingContext(
                    available=True,
                    food_name=latest.food_name,
                    amount_g=latest.amount_g,
                    logged_at=latest.logged_at,
                    minutes_since_feed=mins_ago,
                    reaction=latest.reaction
                )
        except Exception as e:
            logger.warning(f"[CryContextRetriever] Lỗi truy xuất FeedingContext: {e}")
        return FeedingContext(available=False)

    def retrieve_health(self, baby_id: str, user_id: str, now: Optional[datetime] = None) -> HealthContext:
        """Truy xuất nhật ký sức khỏe, triệu chứng sốt và thân nhiệt gần nhất."""
        try:
            records = self.health_service.get_history(baby_id, user_id)
            if records:
                latest = records[0]
                temp_val = None
                if latest.temp is not None:
                    try:
                        temp_val = float(latest.temp)
                    except (ValueError, TypeError):
                        pass
                
                has_fever = (temp_val is not None and temp_val >= 38.0)
                is_high_risk = (temp_val is not None and temp_val >= 38.5) or any(
                    s.lower() in ["co giật", "khó thở", "tím tái", "li bì", "nôn liên tục"]
                    for s in (latest.symptoms or [])
                )

                return HealthContext(
                    available=True,
                    temperature=temp_val,
                    symptoms=latest.symptoms or [],
                    diagnosis=latest.diagnosis,
                    recorded_at=latest.recorded_at,
                    has_fever=has_fever,
                    is_high_risk=is_high_risk
                )
        except Exception as e:
            logger.warning(f"[CryContextRetriever] Lỗi truy xuất HealthContext: {e}")
        return HealthContext(available=False)

    def retrieve_medication(self, baby_id: str, user_id: str, now: Optional[datetime] = None) -> MedicationContext:
        """Truy xuất nhật ký uống thuốc gần nhất."""
        try:
            logs = self.medication_service.get_medication_history(baby_id, user_id)
            if logs:
                latest = logs[0]
                mins_ago = self._calculate_minutes_diff(latest.logged_at, now)
                return MedicationContext(
                    available=True,
                    medication_name=latest.medication_name,
                    dosage=latest.dosage,
                    logged_at=latest.logged_at,
                    minutes_since_medication=mins_ago
                )
        except Exception as e:
            logger.warning(f"[CryContextRetriever] Lỗi truy xuất MedicationContext: {e}")
        return MedicationContext(available=False)

    def retrieve_sleep(self, baby_id: str, user_id: str, now: Optional[datetime] = None) -> SleepContext:
        """Truy xuất dữ liệu giấc ngủ và tính thời gian bé đã thức (wake window)."""
        try:
            db = get_firestore_db()
            if db is not None:
                # Kiểm tra sleep timer hoặc activity logs gần nhất
                doc = db.collection("sleep_timers").document(baby_id).get()
                if doc.exists:
                    data = doc.to_dict() or {}
                    last_end = data.get("last_ended_at") or data.get("started_at")
                    mins_wake = self._calculate_minutes_diff(last_end, now)
                    return SleepContext(
                        available=True,
                        wake_time=last_end,
                        wake_window_minutes=mins_wake,
                        sleep_duration_minutes=data.get("last_duration_minutes")
                    )
        except Exception as e:
            logger.warning(f"[CryContextRetriever] Lỗi truy xuất SleepContext: {e}")
        return SleepContext(available=False)

    def retrieve_bundle(
        self,
        baby_id: Optional[str],
        user_id: Optional[str],
        now: Optional[datetime] = None
    ) -> CryContextBundle:
        """
        Truy xuất toàn bộ các nguồn ngữ cảnh và gói thành CryContextBundle.
        Nếu baby_id hoặc user_id không có, trả về bundle rỗng an toàn.
        """
        if not baby_id or not user_id:
            return CryContextBundle(
                baby_id=baby_id,
                retrieved_at=datetime.now(timezone.utc).isoformat()
            )

        feeding = self.retrieve_feeding(baby_id, user_id, now)
        sleep = self.retrieve_sleep(baby_id, user_id, now)
        health = self.retrieve_health(baby_id, user_id, now)
        medication = self.retrieve_medication(baby_id, user_id, now)

        return CryContextBundle(
            baby_id=baby_id,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            feeding=feeding,
            sleep=sleep,
            health=health,
            medication=medication
        )
