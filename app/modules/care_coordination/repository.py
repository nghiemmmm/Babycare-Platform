"""
Care Coordination Repository - Truy cập Firestore cho Handover Notes, Care Tasks và Care Events.
"""
import uuid
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from google.cloud.firestore import FieldFilter
from app.infrastructure.database import get_firestore_db

logger = logging.getLogger(__name__)


class CareCoordinationRepository:
    HANDOVER_COLLECTION = "handover_notes"
    TASKS_COLLECTION = "care_tasks"
    EVENTS_COLLECTION = "care_events"

    # ─── 1. HANDOVER NOTES ───────────────────────────────────────────────────

    def get_handover_by_date(self, baby_id: str, date_str: str) -> Optional[dict]:
        """Lấy lời dặn bàn giao của bé trong ngày cụ thể (YYYY-MM-DD)."""
        db = get_firestore_db()
        docs = (
            db.collection(self.HANDOVER_COLLECTION)
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .where(filter=FieldFilter("date", "==", date_str))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    def create_or_update_handover(self, data: dict) -> str:
        """Tạo mới hoặc cập nhật lời dặn bàn giao trong ngày."""
        db = get_firestore_db()
        baby_id = data.get("baby_id")
        date_str = data.get("date")

        existing = self.get_handover_by_date(baby_id, date_str)
        if existing:
            doc_id = existing["id"]
            db.collection(self.HANDOVER_COLLECTION).document(doc_id).update({
                **data,
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
            return doc_id
        else:
            doc_id = f"ho_{uuid.uuid4().hex[:8]}"
            db.collection(self.HANDOVER_COLLECTION).document(doc_id).set({
                **data,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
            return doc_id

    # ─── 2. CARE TASKS ───────────────────────────────────────────────────────

    def create_task(self, data: dict) -> str:
        """Tạo một task chăm sóc mới."""
        db = get_firestore_db()
        doc_id = f"task_{uuid.uuid4().hex[:8]}"
        db.collection(self.TASKS_COLLECTION).document(doc_id).set({
            **data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return doc_id

    def get_task_by_id(self, task_id: str) -> Optional[dict]:
        """Lấy chi tiết một task theo ID."""
        db = get_firestore_db()
        doc = db.collection(self.TASKS_COLLECTION).document(task_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        d["id"] = doc.id
        return d

    def list_tasks_by_date(self, baby_id: str, date_str: str) -> List[dict]:
        """Lấy toàn bộ danh sách task trong ngày của bé."""
        db = get_firestore_db()
        docs = (
            db.collection(self.TASKS_COLLECTION)
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .stream()
        )
        tasks = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            scheduled = d.get("scheduled_time", "")
            # Lọc theo ngày (YYYY-MM-DD)
            if scheduled.startswith(date_str):
                tasks.append(d)
        
        # Sắp xếp theo giờ tăng dần
        tasks.sort(key=lambda x: x.get("scheduled_time", ""))
        return tasks

    def update_task(self, task_id: str, updates: dict) -> bool:
        """Cập nhật trạng thái hoặc thông tin của task."""
        db = get_firestore_db()
        doc_ref = db.collection(self.TASKS_COLLECTION).document(task_id)
        doc = doc_ref.get()
        if not doc.exists:
            return False
        doc_ref.update({
            **updates,
            "updated_at": datetime.now(timezone.utc).isoformat()
        })
        return True

    def delete_task(self, task_id: str) -> bool:
        """Xóa task."""
        db = get_firestore_db()
        db.collection(self.TASKS_COLLECTION).document(task_id).delete()
        return True

    # ─── 3. CARE EVENTS ──────────────────────────────────────────────────────

    def create_event(self, data: dict) -> str:
        """Ghi nhận sự kiện chăm sóc thực tế."""
        db = get_firestore_db()
        doc_id = f"evt_{uuid.uuid4().hex[:8]}"
        db.collection(self.EVENTS_COLLECTION).document(doc_id).set({
            **data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return doc_id

    def list_events_by_date(self, baby_id: str, date_str: str, limit: int = 50) -> List[dict]:
        """Lấy danh sách các sự kiện chăm sóc đã diễn ra trong ngày."""
        db = get_firestore_db()
        docs = (
            db.collection(self.EVENTS_COLLECTION)
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .stream()
        )
        events = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            occurred = d.get("occurred_at", d.get("created_at", ""))
            if occurred.startswith(date_str):
                events.append(d)
        
        # Sắp xếp mới nhất lên đầu
        events.sort(key=lambda x: x.get("occurred_at", x.get("created_at", "")), reverse=True)
        return events[:limit]
