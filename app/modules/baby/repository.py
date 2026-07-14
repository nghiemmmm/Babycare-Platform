"""
Baby Repository Module

Handles Firestore collection operations for baby profiles.
"""
from app.shared.repository.base import BaseRepository
from app.modules.baby.schemas import BabyResponse

class BabyRepository(BaseRepository[BabyResponse]):
    def __init__(self):
        super().__init__(collection_name="babies", model_class=BabyResponse)

    def get_babies_by_guardian_id(self, user_id: str) -> list[BabyResponse]:
        """
        Lấy danh sách tất cả các bé mà người dùng có quyền giám hộ.

        Args:
            user_id: UID của người giám hộ.

        Returns:
            Danh sách đối tượng BabyResponse.
        """
        docs = self.db.collection(self.collection_name).where(
            "guardians", "array_contains", user_id
        ).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.model_class(**data))
        return results
