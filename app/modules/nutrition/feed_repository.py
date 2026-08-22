"""
Feed Repository Module
======================
Handles Firestore operations for liquid feeds (breast milk / formula) in the 'nutrition_feeds' collection.
"""
from typing import Optional, List
from google.cloud.firestore import Query
from app.shared.repository.base import BaseRepository
from app.modules.nutrition.schemas import FeedResponse


class FeedRepository(BaseRepository[FeedResponse]):
    def __init__(self):
        super().__init__(collection_name="nutrition_feeds", model_class=FeedResponse)

    def get_by_baby(self, baby_id: str, date: Optional[str] = None, limit: int = 50) -> List[FeedResponse]:
        """
        Lấy danh sách cữ bú của bé theo ngày hoặc gần nhất.
        """
        query = self.db.collection(self.collection_name).where("baby_id", "==", baby_id)
        if date and date != "Today":
            query = query.where("date", "==", date)
        
        docs = query.limit(limit).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            results.append(FeedResponse(
                id=doc.id,
                type=d.get("type", "Formula"),
                details=d.get("details", ""),
                amount=float(d.get("amount", 0.0)),
                time=d.get("time", ""),
                date=d.get("date", "")
            ))
        return results
