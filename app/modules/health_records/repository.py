"""
Health Records Repository Module

Handles Firestore collection operations for baby health records,
health episodes, and time-series health events.
"""
from typing import List, Dict, Any, Optional
from app.shared.repository.base import BaseRepository
from app.modules.health_records.schemas import (
    HealthRecordResponse,
    HealthEpisodeResponse,
    HealthEventResponse
)


class HealthRecordRepository(BaseRepository[HealthRecordResponse]):
    """Repository quản lý các bản ghi bệnh án cũ (Legacy Health Records)."""
    def __init__(self, baby_id: str):
        sub_collection_path = f"babies/{baby_id}/health_records"
        super().__init__(collection_name=sub_collection_path, model_class=HealthRecordResponse)


class HealthEpisodeRepository(BaseRepository[HealthEpisodeResponse]):
    """Repository quản lý các đợt theo dõi sức khỏe theo vòng đời (Health Episodes)."""
    def __init__(self, baby_id: str):
        sub_collection_path = f"babies/{baby_id}/health_episodes"
        super().__init__(collection_name=sub_collection_path, model_class=HealthEpisodeResponse)

    def list_episodes(self, status_filter: Optional[str] = None, limit: int = 100) -> List[HealthEpisodeResponse]:
        """Lấy danh sách các đợt bệnh của bé, có thể lọc theo trạng thái active/resolved."""
        col_ref = self.db.collection(self.collection_name)
        query = col_ref
        if status_filter:
            query = query.where("status", "==", status_filter)
        
        docs = query.limit(limit).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["baby_id"] = self.collection_name.split("/")[1]
            results.append(HealthEpisodeResponse(**data))
        
        # Sắp xếp mới nhất lên trước
        results.sort(key=lambda x: x.started_at or x.created_at or "", reverse=True)
        return results

    def get_active_episode(self) -> Optional[HealthEpisodeResponse]:
        """Lấy đợt bệnh đang theo dõi (active) gần nhất."""
        episodes = self.list_episodes(status_filter="active", limit=1)
        return episodes[0] if episodes else None


class HealthEventRepository(BaseRepository[HealthEventResponse]):
    """Repository quản lý các sự kiện diễn tiến trong một đợt bệnh (Timeline Events)."""
    def __init__(self, baby_id: str, episode_id: str):
        sub_collection_path = f"babies/{baby_id}/health_episodes/{episode_id}/events"
        super().__init__(collection_name=sub_collection_path, model_class=HealthEventResponse)
        self.episode_id = episode_id

    def list_events(self, limit: int = 200) -> List[HealthEventResponse]:
        """Lấy toàn bộ sự kiện theo thứ tự thời gian tăng dần để dựng Timeline."""
        docs = self.db.collection(self.collection_name).limit(limit).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            data["episode_id"] = self.episode_id
            results.append(HealthEventResponse(**data))
        
        # Sắp xếp theo dòng thời gian tăng dần
        results.sort(key=lambda x: x.recorded_at or "")
        return results
