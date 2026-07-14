from typing import TypeVar, Generic, Optional, Any
from google.cloud.firestore import Client
from pydantic import BaseModel
from app.infrastructure.database import get_firestore_db

# Định nghĩa Generic Type đại diện cho Pydantic Schema
ModelType = TypeVar("ModelType", bound=BaseModel)

class BaseRepository(Generic[ModelType]):
    def __init__(self, collection_name: str, model_class: type[ModelType]):
        """
        Base Repository cung cấp các thao tác CRUD cơ bản trên Firebase Firestore.

        Args:
            collection_name: Tên của Firestore collection.
            model_class: Class Pydantic đại diện để validation và gọt dữ liệu.
        """
        self.collection_name = collection_name
        self.model_class = model_class
        self._db: Optional[Client] = None

    @property
    def db(self) -> Client:
        """Lấy Firestore client kết nối."""
        if self._db is None:
            self._db = get_firestore_db()
        return self._db

    def get(self, doc_id: str) -> Optional[ModelType]:
        """
        Lấy thông tin một tài liệu theo ID và map thành Pydantic Object.
        """
        doc_ref = self.db.collection(self.collection_name).document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return self.model_class(**data)
        return None

    def create(self, obj_in: ModelType, doc_id: Optional[str] = None) -> ModelType:
        """
        Tạo mới một tài liệu trên Firestore.
        """
        data = obj_in.model_dump(exclude_none=True)
        # Loại bỏ trường id khỏi dữ liệu lưu trữ nếu có (vì ID là khóa tài liệu)
        data.pop("id", None)
        
        if doc_id:
            doc_ref = self.db.collection(self.collection_name).document(doc_id)
        else:
            doc_ref = self.db.collection(self.collection_name).document()
            
        doc_ref.set(data)
        
        # Gán lại ID mới được tạo và trả về đối tượng Pydantic hoàn chỉnh
        result_data = obj_in.model_dump()
        result_data["id"] = doc_ref.id
        return self.model_class(**result_data)

    def update(self, doc_id: str, obj_in: dict[str, Any]) -> Optional[ModelType]:
        """
        Cập nhật một phần các trường của tài liệu trong Firestore.
        """
        doc_ref = self.db.collection(self.collection_name).document(doc_id)
        # Lọc bỏ giá trị None để tránh ghi đè dữ liệu rác
        update_data = {k: v for k, v in obj_in.items() if v is not None}
        doc_ref.update(update_data)
        
        return self.get(doc_id)

    def delete(self, doc_id: str) -> bool:
        """
        Xóa một tài liệu khỏi Firestore.
        """
        doc_ref = self.db.collection(self.collection_name).document(doc_id)
        doc_ref.delete()
        return True

    def list(self, limit: int = 100) -> list[ModelType]:
        """
        Lấy danh sách các tài liệu trong collection kèm giới hạn số lượng.
        """
        docs = self.db.collection(self.collection_name).limit(limit).stream()
        results = []
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            results.append(self.model_class(**data))
        return results
