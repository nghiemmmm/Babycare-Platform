"""
Guardian Repository - Chịu trách nhiệm truy cập dữ liệu trực tiếp từ Firestore.

Tách 2 collection riêng biệt:
- "guardians": chỉ chứa những người ĐÃ chấp nhận tham gia (thành viên chính thức).
- "invitations": chỉ chứa lời mời đang chờ/đã xử lý (pending/accepted/declined/expired).
Trước đây cả 2 dùng chung 1 collection "guardians", gây khó khăn khi cần chặn mời trùng,
cho phép gửi lại lời mời, hoặc cho lời mời hết hạn một cách rõ ràng.
"""
from typing import List, Optional
from datetime import datetime, timezone
from google.cloud.firestore import FieldFilter
from app.infrastructure.database import get_firestore_db
import uuid


class GuardianRepository:
    COLLECTION = "guardians"
    INVITATIONS_COLLECTION = "invitations"
    BABIES_COLLECTION = "babies"

    # ─── Guardians đã tham gia (active) ────────────────────────────────────

    def list_guardians_by_baby(self, baby_id: str) -> List[dict]:
        """Trả về tất cả guardian documents đã tham gia (Synced) của một bé."""
        db = get_firestore_db()
        docs = db.collection(self.COLLECTION).where(filter=FieldFilter("baby_id", "==", baby_id)).stream()
        results = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            results.append(d)
        return results

    def create_guardian(self, data: dict) -> str:
        """Tạo một guardian document mới (thành viên đã tham gia), trả về document ID."""
        db = get_firestore_db()
        doc_id = f"g_{uuid.uuid4().hex[:8]}"
        db.collection(self.COLLECTION).document(doc_id).set({
            **data,
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return doc_id

    def get_guardian_by_id(self, guardian_id: str) -> Optional[dict]:
        """Lấy guardian document theo ID. Trả về None nếu không tồn tại."""
        db = get_firestore_db()
        doc = db.collection(self.COLLECTION).document(guardian_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        d["id"] = doc.id
        return d

    def get_guardian_by_baby_and_user(self, baby_id: str, user_id: str) -> Optional[dict]:
        """Lấy bản ghi guardian của một user cụ thể trên một bé - dùng để tra vai trò khi
        kiểm tra quyền thao tác (xem app/modules/guardian/permissions.py)."""
        db = get_firestore_db()
        docs = (
            db.collection(self.COLLECTION)
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .where(filter=FieldFilter("user_id", "==", user_id))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    def find_guardian_by_baby_and_email(self, baby_id: str, email: str) -> Optional[dict]:
        """Kiểm tra email đã là guardian chính thức của bé chưa - dùng để chặn mời trùng."""
        db = get_firestore_db()
        docs = (
            db.collection(self.COLLECTION)
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .where(filter=FieldFilter("email", "==", email))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    def delete_guardian(self, guardian_id: str) -> None:
        """Xóa guardian document."""
        db = get_firestore_db()
        db.collection(self.COLLECTION).document(guardian_id).delete()

    def add_to_baby_guardians_list(self, baby_id: str, user_id: str) -> None:
        """Thêm uid vào danh sách guardians[] của bé."""
        db = get_firestore_db()
        baby_ref = db.collection(self.BABIES_COLLECTION).document(baby_id)
        baby_doc = baby_ref.get()
        if baby_doc.exists:
            baby_data = baby_doc.to_dict()
            guardians_list = baby_data.get("guardians", [])
            if user_id not in guardians_list:
                guardians_list.append(user_id)
                baby_ref.update({"guardians": guardians_list})

    def remove_from_baby_guardians_list(self, baby_id: str, user_id: str) -> None:
        """Xóa uid khỏi danh sách guardians[] của bé."""
        db = get_firestore_db()
        baby_ref = db.collection(self.BABIES_COLLECTION).document(baby_id)
        baby_doc = baby_ref.get()
        if baby_doc.exists:
            baby_data = baby_doc.to_dict()
            guardians_list = baby_data.get("guardians", [])
            if user_id in guardians_list:
                guardians_list.remove(user_id)
                baby_ref.update({"guardians": guardians_list})

    # ─── Lời mời (invitations) ──────────────────────────────────────────────

    def create_invitation(self, data: dict) -> str:
        """Tạo một invitation document mới với status mặc định 'pending', trả về ID."""
        db = get_firestore_db()
        doc_ref = db.collection(self.INVITATIONS_COLLECTION).document()
        doc_ref.set({
            **data,
            "status": "pending",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        return doc_ref.id

    def get_invitation_by_id(self, invitation_id: str) -> Optional[dict]:
        db = get_firestore_db()
        doc = db.collection(self.INVITATIONS_COLLECTION).document(invitation_id).get()
        if not doc.exists:
            return None
        d = doc.to_dict()
        d["id"] = doc.id
        return d

    def get_invitation_by_token_hash(self, token_hash: str) -> Optional[dict]:
        """Tra cứu lời mời bằng hash của token công khai trong URL - không bao giờ tra bằng
        token gốc (chỉ lưu hash trong Firestore, tương tự pattern OTP đặt lại mật khẩu)."""
        db = get_firestore_db()
        docs = (
            db.collection(self.INVITATIONS_COLLECTION)
            .where(filter=FieldFilter("token_hash", "==", token_hash))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    def get_pending_invitation_by_email(self, baby_id: str, email: str) -> Optional[dict]:
        """Kiểm tra đã có lời mời 'pending' khác cho đúng email + bé này chưa - chặn mời trùng."""
        db = get_firestore_db()
        docs = (
            db.collection(self.INVITATIONS_COLLECTION)
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .where(filter=FieldFilter("email", "==", email))
            .where(filter=FieldFilter("status", "==", "pending"))
            .limit(1)
            .stream()
        )
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            return d
        return None

    def list_pending_invitations_by_baby(self, baby_id: str) -> List[dict]:
        db = get_firestore_db()
        docs = (
            db.collection(self.INVITATIONS_COLLECTION)
            .where(filter=FieldFilter("baby_id", "==", baby_id))
            .where(filter=FieldFilter("status", "==", "pending"))
            .stream()
        )
        results = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            results.append(d)
        return results

    def update_invitation(self, invitation_id: str, data: dict) -> None:
        db = get_firestore_db()
        db.collection(self.INVITATIONS_COLLECTION).document(invitation_id).update(data)

    def delete_invitation(self, invitation_id: str) -> None:
        db = get_firestore_db()
        db.collection(self.INVITATIONS_COLLECTION).document(invitation_id).delete()
