"""
Health Records Service Module

Handles business logic for:
1. Health Episodes (Vòng đời đợt bệnh: Hô hấp, Tiêu hóa, Da liễu, Mọc răng, Sốt)
2. Time-series Health Events (Dòng thời gian sự kiện theo giờ)
3. Progress Trend Assessment (Phân tích tiến triển: thuyên giảm, ổn định, cần chú ý)
4. AI Pediatric Regimen Generation (Gợi ý phác đồ xử lý ban đầu)
5. Legacy Health Records Compatibility (Tương thích ngược 100%)
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.modules.health_records.schemas import (
    HealthEpisodeCreate,
    HealthEpisodeUpdate,
    HealthEpisodeResponse,
    HealthEpisodeDetailResponse,
    HealthEventCreate,
    HealthEventResponse,
    HealthRecordCreate,
    HealthRecordResponse,
    EpisodeCategoryEnum,
    EventSeverityEnum,
    EventTypeEnum
)
from app.modules.health_records.repository import (
    HealthEpisodeRepository,
    HealthEventRepository,
    HealthRecordRepository
)
from app.modules.baby.service import BabyService
from app.modules.guardian.permissions import ADMIN, GUARDIAN, require_role
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


class HealthRecordService:
    def __init__(self, baby_service: Optional[BabyService] = None):
        self.baby_service = baby_service or BabyService()

    # ─── 1. AI PEDIATRIC TREATMENT GENERATOR ─────────────────────────────────

    def generate_ai_treatment(
        self,
        symptoms: List[str],
        diagnosis: Optional[str] = None,
        baby_name: str = "bé",
        category: str = "general"
    ) -> str:
        """
        AI Backend Generator: Tự động sinh phác đồ chăm sóc chuẩn y khoa
        bao quát 5 nhóm bệnh lý: Hô hấp, Tiêu hóa, Da liễu, Mọc răng, Sốt.
        """
        parts = []
        sym_text = (" ".join(symptoms) + " " + (diagnosis or "") + " " + category).lower()

        # 1. Nhóm Hô hấp (Respiratory)
        if any(w in sym_text for w in ["ho", "họng", "cảm", "phế quản", "respiratory"]):
            parts.append(
                "Dùng siro ho thảo dược nhi khoa, rửa mũi bằng nước muối sinh lý 0.9% ngày 2-3 lần, "
                "cho bé uống nhiều nước ấm và giữ ấm vùng cổ ngực."
            )
        if any(w in sym_text for w in ["sổ mũi", "ngạt", "khò khè"]):
            parts.append("Hút sạch dịch mũi trước khi bú/ngủ và duy trì độ ẩm phòng 55-60%.")

        # 2. Nhóm Tiêu hóa (Digestive)
        if any(w in sym_text for w in ["tiêu chảy", "phân", "nôn", "bụng", "digestive"]):
            parts.append(
                "Cho bé uống Oresol bù điện giải từng thìa nhỏ rải rác trong ngày, bổ sung men vi sinh, "
                "cho ăn thức ăn lỏng dễ tiêu và chia thành nhiều cữ nhỏ."
            )

        # 3. Nhóm Da liễu & Dị ứng (Dermatology)
        if any(w in sym_text for w in ["mẩn", "dị ứng", "ban", "chàm", "hăm", "dermatology"]):
            parts.append(
                "Giữ da bé sạch thoáng, thoa kem dưỡng ẩm/kem dịu da chuyên dụng, tắm nước ấm nhẹ nhàng "
                "và tránh tiếp xúc các chất gây kích ứng."
            )

        # 4. Nhóm Mọc răng & Quấy khóc (Teething)
        if any(w in sym_text for w in ["mọc răng", "nướu", "dãi", "teething"]):
            parts.append("Cho ngậm nướu lạnh sạch, mát-xa nướu nhẹ nhàng và giữ vệ sinh khoang miệng cho bé.")

        # 5. Nhóm Sốt & Thân nhiệt (Fever)
        if any(w in sym_text for w in ["sốt", "fever", "nóng"]):
            if "39.5" in sym_text or "sốt cao" in sym_text:
                parts.append(
                    "⚠️ Sốt cao: Cho bé uống Paracetamol liều 10-15mg/kg (theo chỉ định), "
                    "chườm ấm trán, nách, bẹn và đưa bé đến cơ sở y tế nếu sốt kéo dài >48h."
                )
            else:
                parts.append(
                    "Chườm ấm trán nách, giữ phòng thoáng mát, cho bú nhiều cữ nhỏ và theo dõi thân nhiệt mỗi 30-60 phút."
                )

        if not parts:
            parts.append(f"Cho {baby_name} nghỉ ngơi, theo dõi sinh hoạt và bổ sung đầy đủ dinh dưỡng/nước.")

        return " ".join(parts)

    # ─── 2. PROGRESS TREND ASSESSMENT ────────────────────────────────────────

    def calculate_progress_trend(self, events: List[HealthEventResponse], category: str) -> tuple[str, str]:
        """
        Thuật toán đánh giá xu hướng tiến triển sức khỏe:
        - improving (Thuyên giảm 🌿)
        - stable (Ổn định ⚖️)
        - worsening (Cần chú ý theo dõi thêm ⚠️)
        """
        if not events:
            return "stable", "Đang bắt đầu theo dõi diễn biến sức khỏe của bé."

        recent_events = events[-5:]

        # A. Nhóm Sốt
        if category == EpisodeCategoryEnum.FEVER.value:
            temp_events = [e for e in recent_events if e.metric_value is not None]
            if len(temp_events) >= 2:
                latest_temp = temp_events[-1].metric_value
                prev_temp = temp_events[-2].metric_value
                if latest_temp < 37.5:
                    return "improving", f"Thân nhiệt đã hạ về mức bình thường ({latest_temp}°C). Bé đang hồi phục rất tốt!"
                elif latest_temp < prev_temp:
                    return "improving", f"Thân nhiệt đang có chiều hướng giảm dần từ {prev_temp}°C xuống {latest_temp}°C."
                elif latest_temp >= 38.5 and latest_temp >= prev_temp:
                    return "worsening", f"Thân nhiệt đang sốt cao ({latest_temp}°C). Cần chườm ấm và cho uống hạ sốt đúng cữ."
            elif temp_events and temp_events[-1].metric_value < 37.5:
                return "improving", "Thân nhiệt đang ở mức ổn định an toàn."

        # B. Nhóm Hô hấp (Ho, Sổ mũi)
        if category == EpisodeCategoryEnum.RESPIRATORY.value:
            sym_events = [e for e in recent_events if e.severity is not None]
            if sym_events:
                latest_sev = sym_events[-1].severity
                if latest_sev in [EventSeverityEnum.NONE.value, EventSeverityEnum.MILD.value]:
                    return "improving", "Cơn ho và dịch mũi đã thuyên giảm rõ rệt, tiếng thở êm hơn."
                elif latest_sev == EventSeverityEnum.SEVERE.value:
                    return "worsening", "Cơn ho hoặc nghẹt mũi còn nhiều, cần rửa mũi và cho uống siro đúng giờ."

        # C. Nhóm Tiêu hóa
        if category == EpisodeCategoryEnum.DIGESTIVE.value:
            count_events = [e for e in recent_events if e.count_value is not None]
            if len(count_events) >= 2:
                if count_events[-1].count_value < count_events[-2].count_value:
                    return "improving", "Số lần đi ngoài/nôn trớ trong ngày đang giảm dần, hệ tiêu hóa đang ổn định."
                elif count_events[-1].count_value >= 4:
                    return "worsening", f"Số lần đi ngoài trong ngày còn nhiều ({count_events[-1].count_value} lần). Cần tiếp tục bù điện giải."

        # D. Nhóm Da liễu
        if category == EpisodeCategoryEnum.DERMATOLOGY.value:
            sym_events = [e for e in recent_events if e.severity is not None]
            if sym_events and sym_events[-1].severity in ["mild", "none"]:
                return "improving", "Vết mẩn đỏ đang dịu đi và khô se mài, bé bớt ngứa khó chịu."

        return "stable", "Các triệu chứng đang trong tầm kiểm soát ổn định. Tiếp tục chăm sóc theo phác đồ."

    # ─── 3. HEALTH EPISODES MANAGEMENT ───────────────────────────────────────

    def create_episode(
        self,
        baby_id: str,
        episode_in: HealthEpisodeCreate,
        user_id: str,
        user_name: str = "Phụ huynh"
    ) -> HealthEpisodeDetailResponse:
        """Khởi tạo một đợt theo dõi sức khỏe mới cho bé kèm sự kiện ban đầu."""
        baby = self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        baby_name = baby.name if baby else "bé"

        now_utc = datetime.now(timezone.utc).isoformat()
        started_at = episode_in.started_at or now_utc

        treatment = episode_in.treatment
        if not treatment:
            treatment = self.generate_ai_treatment(
                symptoms=episode_in.initial_symptoms,
                diagnosis=episode_in.diagnosis or episode_in.title,
                baby_name=baby_name,
                category=episode_in.category
            )

        repo = HealthEpisodeRepository(baby_id)
        episode_payload = {
            "category": episode_in.category,
            "title": episode_in.title,
            "status": "active",
            "progress_status": "stable",
            "started_at": started_at,
            "resolved_at": None,
            "initial_symptoms": episode_in.initial_symptoms,
            "diagnosis": episode_in.diagnosis,
            "treatment": treatment,
            "doctor_name": episode_in.doctor_name or "AI Y Khoa Gợi Ý",
            "notes": episode_in.notes or "",
            "primary_metric_name": episode_in.primary_metric_name or "temperature",
            "created_at": now_utc,
            "updated_at": now_utc
        }

        # Lưu Episode
        episode_ref = repo.db.collection(repo.collection_name).document()
        episode_id = episode_ref.id
        episode_payload["id"] = episode_id
        episode_payload["baby_id"] = baby_id
        episode_ref.set(episode_payload)

        # Tạo sự kiện khởi tạo ban đầu vào sub-collection events
        events_repo = HealthEventRepository(baby_id, episode_id)
        first_event_payload = {
            "event_type": EventTypeEnum.MEASUREMENT.value if episode_in.initial_temp else EventTypeEnum.SYMPTOM_CHECK.value,
            "recorded_at": started_at,
            "recorded_by_name": user_name,
            "metric_value": episode_in.initial_temp,
            "count_value": None,
            "symptom_name": episode_in.initial_symptoms[0] if episode_in.initial_symptoms else "Phát hiện triệu chứng",
            "severity": episode_in.initial_severity or EventSeverityEnum.MILD.value,
            "descriptor": episode_in.initial_descriptor or "Ghi nhận khởi phát đợt theo dõi sức khỏe",
            "action_or_med_name": None,
            "notes": f"Khởi tạo bởi {user_name}"
        }
        ev_ref = events_repo.db.collection(events_repo.collection_name).document()
        first_event_payload["id"] = ev_ref.id
        first_event_payload["episode_id"] = episode_id
        ev_ref.set(first_event_payload)

        initial_event = HealthEventResponse(**first_event_payload)
        return HealthEpisodeDetailResponse(
            **episode_payload,
            events_count=1,
            latest_event=initial_event,
            events=[initial_event],
            progress_summary="Đang bắt đầu theo dõi diễn biến sức khỏe của bé."
        )

    def get_active_episode(self, baby_id: str, user_id: str) -> Optional[HealthEpisodeDetailResponse]:
        """Lấy đợt bệnh đang theo dõi (active) kèm toàn bộ chuỗi timeline sự kiện."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = HealthEpisodeRepository(baby_id)
        active_ep = repo.get_active_episode()
        if not active_ep:
            return None
        return self.get_episode_detail(baby_id, active_ep.id, user_id)

    def list_episodes(
        self,
        baby_id: str,
        user_id: str,
        status_filter: Optional[str] = None
    ) -> List[HealthEpisodeResponse]:
        """Lấy danh sách các đợt bệnh (active hoặc resolved)."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = HealthEpisodeRepository(baby_id)
        episodes = repo.list_episodes(status_filter=status_filter)

        # Gắn thêm số lượng events và latest event cho từng đợt
        for ep in episodes:
            if ep.id:
                ev_repo = HealthEventRepository(baby_id, ep.id)
                events = ev_repo.list_events(limit=50)
                ep.events_count = len(events)
                if events:
                    ep.latest_event = events[-1]
        return episodes

    def get_episode_detail(self, baby_id: str, episode_id: str, user_id: str) -> HealthEpisodeDetailResponse:
        """Lấy chi tiết đợt bệnh kèm toàn bộ dòng thời gian sự kiện (Timeline)."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = HealthEpisodeRepository(baby_id)
        doc = repo.get(episode_id)
        if not doc:
            raise EntityNotFoundError(f"Không tìm thấy đợt theo dõi sức khỏe mã: {episode_id}")

        ev_repo = HealthEventRepository(baby_id, episode_id)
        events = ev_repo.list_events(limit=300)

        # Tính toán xu hướng tiến triển
        trend, summary = self.calculate_progress_trend(events, doc.category)
        if doc.status == "active" and doc.progress_status != trend:
            repo.update(episode_id, {"progress_status": trend})
            doc.progress_status = trend

        doc_dict = doc.model_dump()
        doc_dict["events_count"] = len(events)
        doc_dict["latest_event"] = events[-1] if events else None
        return HealthEpisodeDetailResponse(
            **doc_dict,
            events=events,
            progress_summary=summary
        )

    def add_event(
        self,
        baby_id: str,
        episode_id: str,
        event_in: HealthEventCreate,
        user_id: str,
        user_name: str = "Phụ huynh"
    ) -> HealthEventResponse:
        """Thêm một sự kiện mới vào dòng thời gian của đợt bệnh (đo nhiệt độ, cữ ho, cữ thuốc, rửa mũi...)."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)

        repo = HealthEpisodeRepository(baby_id)
        ep = repo.get(episode_id)
        if not ep:
            raise EntityNotFoundError(f"Không tìm thấy đợt theo dõi sức khỏe mã: {episode_id}")

        now_utc = datetime.now(timezone.utc).isoformat()
        ev_repo = HealthEventRepository(baby_id, episode_id)
        
        event_payload = event_in.model_dump()
        event_payload["recorded_at"] = event_payload.get("recorded_at") or now_utc
        event_payload["recorded_by_name"] = event_payload.get("recorded_by_name") or user_name
        event_payload["episode_id"] = episode_id

        ev_ref = ev_repo.db.collection(ev_repo.collection_name).document()
        event_payload["id"] = ev_ref.id
        ev_ref.set(event_payload)

        # Cập nhật updated_at trên đợt bệnh và tính toán lại xu hướng tiến triển
        all_events = ev_repo.list_events(limit=50)
        trend, _ = self.calculate_progress_trend(all_events, ep.category)
        repo.update(episode_id, {
            "updated_at": now_utc,
            "progress_status": trend
        })

        return HealthEventResponse(**event_payload)

    def resolve_episode(
        self,
        baby_id: str,
        episode_id: str,
        user_id: str,
        user_name: str = "Phụ huynh"
    ) -> HealthEpisodeResponse:
        """Đánh dấu đợt bệnh đã khỏi hoàn toàn (Bé đã khỏi bệnh)."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)

        repo = HealthEpisodeRepository(baby_id)
        ep = repo.get(episode_id)
        if not ep:
            raise EntityNotFoundError(f"Không tìm thấy đợt theo dõi sức khỏe mã: {episode_id}")

        now_utc = datetime.now(timezone.utc).isoformat()
        repo.update(episode_id, {
            "status": "resolved",
            "progress_status": "improving",
            "resolved_at": now_utc,
            "updated_at": now_utc
        })

        # Ghi nhận sự kiện kết thúc vào timeline
        ev_repo = HealthEventRepository(baby_id, episode_id)
        finish_event = {
            "event_type": EventTypeEnum.NOTE.value,
            "recorded_at": now_utc,
            "recorded_by_name": user_name,
            "descriptor": "Đánh dấu đợt bệnh đã khỏi hoàn toàn. Bé đã khỏe mạnh và sinh hoạt bình thường.",
            "severity": EventSeverityEnum.NONE.value,
            "notes": f"Xác nhận khỏi bệnh bởi {user_name}"
        }
        ev_ref = ev_repo.db.collection(ev_repo.collection_name).document()
        finish_event["id"] = ev_ref.id
        finish_event["episode_id"] = episode_id
        ev_ref.set(finish_event)

        updated = repo.get(episode_id)
        return updated

    # ─── 4. LEGACY HEALTH RECORD (COMPATIBILITY) ──────────────────────────────

    def add_record(self, baby_id: str, record_in: HealthRecordCreate, user_id: str) -> HealthRecordResponse:
        """Hỗ trợ API cũ add_record: Lưu vào health_records và đồng thời tạo HealthEpisode."""
        baby = self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        baby_name = baby.name if baby else "bé"

        treatment = record_in.treatment
        if not treatment:
            treatment = self.generate_ai_treatment(
                symptoms=record_in.symptoms,
                diagnosis=record_in.diagnosis,
                baby_name=baby_name
            )

        now = datetime.now(timezone.utc).isoformat()
        repo = HealthRecordRepository(baby_id)
        record_obj = HealthRecordResponse(
            symptoms=record_in.symptoms,
            diagnosis=record_in.diagnosis,
            treatment=treatment,
            doctor_name=record_in.doctor_name or "AI Y Khoa Gợi Ý",
            notes=record_in.notes,
            temp=record_in.temp,
            status=record_in.status or "Confirmed",
            recorded_at=now
        )
        created = repo.create(record_obj)

        # Đồng thời tạo HealthEpisode mới để hiển thị ngay trên mô hình mới
        try:
            category = "fever" if (record_in.temp and record_in.temp >= 38.0) else "respiratory"
            diag = record_in.diagnosis or "Theo dõi sức khỏe"
            diag_lower = diag.lower()
            if any(w in diag_lower for w in ["tiêu", "bụng", "nôn", "phân"]):
                category = "digestive"
            elif any(w in diag_lower for w in ["da", "chàm", "mẩn", "dị ứng"]):
                category = "dermatology"
            elif any(w in diag_lower for w in ["răng", "nướu"]):
                category = "teething"

            ep_create = HealthEpisodeCreate(
                category=category,
                title=diag,
                initial_symptoms=record_in.symptoms,
                diagnosis=record_in.diagnosis,
                treatment=treatment,
                doctor_name=record_in.doctor_name,
                initial_temp=record_in.temp,
                status="active" if record_in.status == "Confirmed" else "resolved"
            )
            self.create_episode(baby_id, ep_create, user_id)
        except Exception as e:
            logger.warning(f"Auto-migration to HealthEpisode failed non-critically: {e}")

        return created

    def get_history(self, baby_id: str, user_id: str) -> List[HealthRecordResponse]:
        """Lấy toàn bộ lịch sử bệnh án (API cũ)."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = HealthRecordRepository(baby_id)
        records = repo.list(limit=500)
        records.sort(key=lambda x: x.recorded_at, reverse=True)
        return records

    def update_record(self, baby_id: str, record_id: str, update_data: dict, user_id: str) -> HealthRecordResponse:
        """Cập nhật thông tin bệnh án (API cũ)."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        repo = HealthRecordRepository(baby_id)
        existing = repo.get(record_id)
        if not existing:
            raise EntityNotFoundError("Không tìm thấy thông tin bệnh án cần cập nhật")
        return repo.update(record_id, update_data)

    def delete_record(self, baby_id: str, record_id: str, user_id: str) -> bool:
        """Xóa bản ghi bệnh án (API cũ)."""
        self.baby_service.get_baby_by_id(baby_id, user_id)
        require_role(baby_id, user_id, ADMIN, GUARDIAN)
        repo = HealthRecordRepository(baby_id)
        record = repo.get(record_id)
        if not record:
            raise EntityNotFoundError("Không tìm thấy thông tin bệnh án cần xóa")
        return repo.delete(record_id)
