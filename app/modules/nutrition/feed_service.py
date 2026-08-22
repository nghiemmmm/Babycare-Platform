"""
Feed Service Module
===================
Handles business logic and permission checking for liquid feeding logs (breast milk / formula).
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
from app.modules.nutrition.schemas import FeedCreate, FeedResponse, FeedCreateResponse
from app.modules.nutrition.feed_repository import FeedRepository
from app.modules.baby.service import BabyService
from app.shared.exceptions import EntityNotFoundError

logger = logging.getLogger(__name__)


class FeedService:
    def __init__(self, baby_service: Optional[BabyService] = None, repo: Optional[FeedRepository] = None):
        self.baby_service = baby_service or BabyService()
        self.repo = repo or FeedRepository()

    def add_feed_log(self, baby_id: str, feed_in: FeedCreate, user_id: str) -> FeedCreateResponse:
        """
        Ghi nhận cữ bú sữa mới sau khi kiểm tra quyền giám hộ.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        
        feed_id = f"feed_{uuid.uuid4().hex[:8]}"
        doc_ref = self.repo.db.collection(self.repo.collection_name).document(feed_id)
        
        now = datetime.now(timezone.utc)
        doc_data = {
            "baby_id": baby_id,
            "type": feed_in.type,
            "details": feed_in.details,
            "amount": feed_in.amount,
            "time": feed_in.time or now.strftime("%H:%M"),
            "date": now.date().isoformat(),
            "created_at": now.isoformat()
        }
        doc_ref.set(doc_data)
        return FeedCreateResponse(success=True, feed_id=feed_id)

    def get_feed_history(self, baby_id: str, user_id: str, date: Optional[str] = None, limit: int = 50) -> List[FeedResponse]:
        """
        Lấy lịch sử bú sữa của bé.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        return self.repo.get_by_baby(baby_id, date=date, limit=limit)

    def delete_feed_log(self, baby_id: str, feed_id: str, user_id: str) -> bool:
        """
        Xóa một bản ghi cữ bú.
        """
        self.baby_service.get_baby_by_id(baby_id, user_id)
        doc_ref = self.repo.db.collection(self.repo.collection_name).document(feed_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise EntityNotFoundError("Không tìm thấy bản ghi cữ bú")
        doc_ref.delete()
        return True
