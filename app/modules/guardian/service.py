import logging
from typing import List
from fastapi import HTTPException

from app.modules.guardian.repository import GuardianRepository
from app.modules.guardian.schemas import GuardianResponse, InviteResponse, MessageResponse
from app.modules.baby.repository import BabyRepository
from app.core.email_service import EmailService

logger = logging.getLogger(__name__)


class GuardianService:
    def __init__(self):
        self.repo = GuardianRepository()
        self.baby_repo = BabyRepository()
        self.email_svc = EmailService()

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
        role: str,
        inviter_name: str = "Phụ huynh"
    ) -> InviteResponse:
        """
        Gửi lời mời và lưu invitation vào Firestore, đồng thời gửi email thông báo qua SMTP.
        """
        invitation_id = self.repo.create_invitation({
            "baby_id": baby_id,
            "name": name,
            "email": email,
            "role": role,
            "status": "Invited"
        })
        self.repo.add_to_baby_guardians_list(baby_id, invitation_id)

        # Lấy thông tin bé để gửi mail
        try:
            baby = self.baby_repo.get(baby_id)
            baby_name = baby.name if baby else "Bé"
        except Exception:
            baby_name = "Bé"

        # Kích hoạt gửi email SMTP
        try:
            sent_ok = self.email_svc.send_guardian_invitation_email(
                to_email=email,
                guardian_name=name,
                baby_name=baby_name,
                role=role,
                inviter_name=inviter_name,
                invitation_id=invitation_id
            )
            msg = "Đã gửi email mời thành công" if sent_ok else "Đã lưu lời mời nhưng gửi email thất bại (kiểm tra lại SMTP)"
        except Exception as e:
            logger.error(f"Lỗi khi gửi email lời mời: {e}")
            msg = "Đã lưu lời mời nhưng có lỗi khi gửi email"

        return InviteResponse(
            success=True,
            message=msg,
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

    def accept_invitation(
        self,
        invitation_id: str,
        user_id: str,
        user_email: str = ""
    ) -> MessageResponse:
        """
        Chấp nhận lời mời tham gia chăm sóc bé:
        - Cập nhật trạng thái lời mời sang 'Synced'
        - Ghi nhận user_id của người chấp nhận
        - Bổ sung user_id vào danh sách guardians[] của bé trên Firestore
        """
        invitation = self.repo.get_by_id(invitation_id)
        if not invitation:
            raise HTTPException(status_code=404, detail="Không tìm thấy lời mời hoặc lời mời không tồn tại.")

        if invitation.get("status") == "Synced":
            return MessageResponse(
                success=True,
                message="Bạn đã là người giám hộ chính thức trước đó."
            )

        baby_id = invitation.get("baby_id")

        # 1. Cập nhật bản ghi lời mời
        self.repo.update_status_and_user(invitation_id, user_id=user_id, status="Synced")

        # 2. Bổ sung user_id vào guardians list của bé
        if baby_id:
            self.repo.add_to_baby_guardians_list(baby_id, user_id)

        return MessageResponse(
            success=True,
            message="Chấp nhận lời mời thành công! Bạn đã chính thức tham gia chăm sóc bé."
        )
