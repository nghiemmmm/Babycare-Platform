"""
Guardian Service - Chứa toàn bộ business logic liên quan đến Người giám hộ.
Gọi vào GuardianRepository để truy cập dữ liệu, không truy cập Firestore trực tiếp.
"""
from typing import List
from fastapi import HTTPException

from app.modules.guardian.repository import GuardianRepository
from app.modules.guardian.schemas import GuardianResponse, InviteResponse, MessageResponse


class GuardianService:
    def __init__(self):
        self.repo = GuardianRepository()

    def list_guardians(
        self,
        baby_id: str,
        fallback_name: str = "Elena",
        fallback_email: str = "mom@family.com",
        user_id: str = ""
    ) -> List[GuardianResponse]:
        """
        Lấy danh sách người giám hộ của bé.
        Nếu chưa có, tự động tạo Admin mặc định cho người tạo bé.
        """
        raw = self.repo.list_by_baby(baby_id)

        if not raw:
            # Tạo ADMIN mặc định cho người sở hữu bé
            g_id = self.repo.create({
                "baby_id": baby_id,
                "user_id": user_id,
                "name": fallback_name,
                "email": fallback_email,
                "role": "ADMIN",
                "status": "Synced"
            })
            return [GuardianResponse(
                id=g_id,
                name=fallback_name,
                email=fallback_email,
                role="ADMIN",
                status="Synced"
            )]

        return [
            GuardianResponse(
                id=g["id"],
                name=g.get("name", ""),
                email=g.get("email", ""),
                role=g.get("role", "GUARDIAN"),
                status=g.get("status", "Synced")
            )
            for g in raw
        ]

    def invite_guardian(
        self,
        baby_id: str,
        name: str,
        email: str,
        role: str
    ) -> InviteResponse:
        """
        Gửi lời mời và lưu invitation vào Firestore.
        Cập nhật danh sách guardians của bé.
        """
        invitation_id = self.repo.create_invitation({
            "baby_id": baby_id,
            "name": name,
            "email": email,
            "role": role
        })
        self.repo.add_to_baby_guardians_list(baby_id, invitation_id)

        return InviteResponse(
            success=True,
            message="Invitation email dispatched successfully",
            invitation_id=invitation_id
        )

    def remove_guardian(self, baby_id: str, guardian_id: str) -> MessageResponse:
        """
        Xóa quyền truy cập của người giám hộ.
        Ném 404 nếu không tìm thấy.
        """
        existing = self.repo.get_by_id(guardian_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Guardian not found")

        self.repo.delete(guardian_id)
        self.repo.remove_from_baby_guardians_list(baby_id, guardian_id)

        return MessageResponse(
            success=True,
            message="Caregiver removed from family circle"
        )
