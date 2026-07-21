"""
Guardian Repository - Chịu trách nhiệm truy cập dữ liệu trực tiếp từ Firestore.
Mọi thao tác với collection "guardians" và "babies" đều nằm ở đây.
"""
from typing import List, Optional
from datetime import datetime, timezone
from app.infrastructure.database import get_firestore_db
import uuid


class GuardianRepository:
    COLLECTION = "guardians"
    BABIES_COLLECTION = "babies"

    def list_by_baby(self, baby_id: str) -> List[dict]:
        """Trả về tất cả guardian documents của một bé."""
        db = get_firestore_db()
        docs = db.collection(self.COLLECTION).where("baby_id", "==", baby_id).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            results.append(d)
        return results

    def create(self, data: dict) -> str:
        """Tạo một guardian document mới, trả về document ID."""
        db = get_firestore_db()
        doc_id = f"g_{uuid.uuid4().hex[:8]}"
        db.collection(self.COLLECTION).document(doc_id).set({
            **data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return doc_id

    def create_invitation(self, data: dict) -> str:
        """Tạo một invitation document, trả về invitation ID."""
        db = get_firestore_db()
        inv_id = f"invite_{uuid.uuid4().hex[:4]}"
        db.collection(self.COLLECTION).document(inv_id).set({
            **data,
            "status": "Invited",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return inv_id

    def get_by_id(self, guardian_id: str) -> Optional[dict]:
        """Lấy guardian document theo ID. Trả về None nếu không tồn tại."""
        db = get_firestore_db()
        doc = db.collection(self.COLLECTION).document(guardian_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        d["id"] = doc.id
        return d

    def delete(self, guardian_id: str) -> None:
        """Xóa guardian document."""
        db = get_firestore_db()
        db.collection(self.COLLECTION).document(guardian_id).delete()

    def add_to_baby_guardians_list(self, baby_id: str, guardian_id: str) -> None:
        """Thêm guardian ID vào danh sách guardians[] của bé."""
        db = get_firestore_db()
        baby_ref = db.collection(self.BABIES_COLLECTION).document(baby_id)
        baby_doc = baby_ref.get()
        if baby_doc.exists:
            baby_data = baby_doc.to_dict()
            guardians_list = baby_data.get("guardians", [])
            if guardian_id not in guardians_list:
                guardians_list.append(guardian_id)
                baby_ref.update({"guardians": guardians_list})

    def remove_from_baby_guardians_list(self, baby_id: str, guardian_id: str) -> None:
        """Xóa guardian ID khỏi danh sách guardians[] của bé."""
        db = get_firestore_db()
        baby_ref = db.collection(self.BABIES_COLLECTION).document(baby_id)
        baby_doc = baby_ref.get()
        if baby_doc.exists:
            baby_data = baby_doc.to_dict()
            guardians_list = baby_data.get("guardians", [])
            if guardian_id in guardians_list:
                guardians_list.remove(guardian_id)
                baby_ref.update({"guardians": guardians_list})
