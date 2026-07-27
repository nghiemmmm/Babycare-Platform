"""
Notification Service - ghi & đọc thông báo trong Firestore collection "notifications", lọc
theo `recipient_uid` (gắn với một người dùng cụ thể) thay vì chỉ theo baby_id như
app/modules/dashboard/aggregator.py. Dùng cho các sự kiện không nhất thiết xảy ra khi người
nhận đang mở đúng hồ sơ bé liên quan (vd. lời mời guardian được chấp nhận/từ chối trong khi
người mời có thể đang xem hồ sơ một bé khác, hoặc không mở app).
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from google.cloud.firestore import FieldFilter
from app.infrastructure.database import get_firestore_db
from app.modules.dashboard.schemas import NotificationResponse

logger = logging.getLogger(__name__)

COLLECTION = "notifications"


def notify_user(
    recipient_uid: str,
    title: str,
    message: str,
    notif_type: str = "system",
    baby_id: Optional[str] = None,
    action_url: Optional[str] = None,
) -> None:
    """
    Ghi một thông báo mới gắn với recipient_uid. Không raise lỗi ra ngoài nếu Firestore lỗi -
    đây luôn là tác vụ phụ đi kèm một hành động chính (vd. chấp nhận lời mời), không nên làm
    fail cả request chỉ vì ghi thông báo thất bại.
    """
    try:
        db = get_firestore_db()
        db.collection(COLLECTION).document().set({
            "recipient_uid": recipient_uid,
            "baby_id": baby_id,
            "title": title,
            "message": message,
            "type": notif_type,
            "action_url": action_url,
            "read": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Không thể ghi thông báo cho {recipient_uid}: {e}")


def get_notifications_for_user(recipient_uid: str) -> List[NotificationResponse]:
    """Lấy toàn bộ thông báo của một người dùng, mới nhất lên trước."""
    db = get_firestore_db()
    docs = (
        db.collection(COLLECTION)
        .where(filter=FieldFilter("recipient_uid", "==", recipient_uid))
        .stream()
    )
    results = []
    for doc in docs:
        d = doc.to_dict()
        results.append(
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
    results.sort(key=lambda x: x.created_at, reverse=True)
    return results


def mark_as_read(notification_id: str) -> bool:
    """Đánh dấu một thông báo là đã đọc."""
    try:
        db = get_firestore_db()
        doc_ref = db.collection(COLLECTION).document(notification_id)
        if doc_ref.get().exists:
            doc_ref.update({"read": True})
        return True
    except Exception as e:
        logger.error(f"Error marking notification {notification_id} as read: {e}")
        return False
