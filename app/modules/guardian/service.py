"""
Guardian Service - Business logic cho vòng tròn người chăm sóc bé: mời qua email, chấp
nhận/từ chối lời mời qua trang xác nhận công khai /invite/{token} (không phải link GET thực
thi trực tiếp trong email - tránh bị email client/security scanner tự động prefetch link kích
hoạt nhầm accept/decline), và báo lại cho người mời qua chuông thông báo khi có phản hồi.
"""
import hashlib
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import HTTPException

from app.core.config import settings
from app.core.email_service import EmailService
from app.modules.auth.schemas import UserRecord
from app.modules.baby.repository import BabyRepository
from app.modules.guardian.permissions import ADMIN, require_role
from app.modules.guardian.repository import GuardianRepository
from app.modules.guardian.schemas import (
    GuardianResponse,
    InvitationPublicInfo,
    InviteResponse,
    MessageResponse,
)
from app.modules.notification.service import notify_user

logger = logging.getLogger(__name__)

INVITE_TOKEN_BYTES = 32
INVITE_TTL_DAYS = 7


def _generate_invite_token() -> str:
    """Sinh token mời ngẫu nhiên bằng CSPRNG - đủ dài để không thể đoán/brute-force qua URL,
    khác hẳn ID ngắn `invite_<4 hex>` trước đây (chỉ 65536 khả năng)."""
    return secrets.token_urlsafe(INVITE_TOKEN_BYTES)


def _hash_token(token: str) -> str:
    """Băm token trước khi lưu Firestore, không lưu token gốc dạng plaintext - cùng nguyên
    tắc với pattern OTP đặt lại mật khẩu ở app/modules/auth/service.py."""
    return hashlib.sha256(token.encode()).hexdigest()


class GuardianService:
    def __init__(self):
        self.repo = GuardianRepository()
        self.baby_repo = BabyRepository()
        self.email_svc = EmailService()

    # ─── Danh sách ──────────────────────────────────────────────────────────

    def list_guardians(
        self,
        baby_id: str,
        fallback_name: str = "Elena",
        fallback_email: str = "mom@family.com",
        user_id: str = ""
    ) -> List[GuardianResponse]:
        """
        Lấy danh sách người giám hộ đã tham gia (Synced) + lời mời đang chờ (Invited) của bé.
        Nếu chưa có guardian nào, tự động tạo Admin mặc định cho người tạo bé.
        """
        active = self.repo.list_guardians_by_baby(baby_id)

        if not active:
            g_id = self.repo.create_guardian({
                "baby_id": baby_id,
                "user_id": user_id,
                "name": fallback_name,
                "email": fallback_email,
                "role": ADMIN,
                "status": "Synced"
            })
            active = [{
                "id": g_id,
                "name": fallback_name,
                "email": fallback_email,
                "role": ADMIN,
                "status": "Synced"
            }]

        pending = self.repo.list_pending_invitations_by_baby(baby_id)

        results = [
            GuardianResponse(
                id=g["id"],
                name=g.get("name", ""),
                email=g.get("email", ""),
                role=g.get("role", "GUARDIAN"),
                status=g.get("status", "Synced")
            )
            for g in active
        ]
        results += [
            GuardianResponse(
                id=inv["id"],
                name=inv.get("name", ""),
                email=inv.get("email", ""),
                role=inv.get("role", "GUARDIAN"),
                status="Invited"
            )
            for inv in pending
        ]
        return results

    # ─── Mời ────────────────────────────────────────────────────────────────

    def invite_guardian(
        self,
        baby_id: str,
        name: str,
        email: str,
        role: str,
        invited_by_uid: str,
        inviter_name: str = "Phụ huynh"
    ) -> InviteResponse:
        """
        Tạo lời mời (collection "invitations", tách khỏi guardians đang hoạt động) và gửi
        email dẫn tới trang xác nhận công khai /invite/{token}. Chỉ ADMIN của bé mới được mời
        thêm người khác. Chặn mời trùng: email đã là guardian của bé, hoặc đã có lời mời
        "pending" khác chưa xử lý cho đúng email + bé này.
        """
        require_role(baby_id, invited_by_uid, ADMIN)

        if self.repo.find_guardian_by_baby_and_email(baby_id, email):
            raise HTTPException(status_code=409, detail="Email này đã là thành viên của bé.")
        if self.repo.get_pending_invitation_by_email(baby_id, email):
            raise HTTPException(status_code=409, detail="Đã có lời mời đang chờ xử lý cho email này.")

        token = _generate_invite_token()
        now = datetime.now(timezone.utc)
        invitation_id = self.repo.create_invitation({
            "baby_id": baby_id,
            "name": name,
            "email": email,
            "role": role,
            "invited_by": invited_by_uid,
            "token_hash": _hash_token(token),
            "expires_at": (now + timedelta(days=INVITE_TTL_DAYS)).isoformat(),
        })

        try:
            baby = self.baby_repo.get(baby_id)
            baby_name = baby.name if baby else "Bé"
        except Exception:
            baby_name = "Bé"

        invite_link = f"{settings.FRONTEND_URL}/invite/{token}"
        try:
            sent_ok = self.email_svc.send_guardian_invitation_email(
                to_email=email,
                guardian_name=name,
                baby_name=baby_name,
                role=role,
                inviter_name=inviter_name,
                invite_link=invite_link
            )
            msg = "Đã gửi email mời thành công" if sent_ok else "Đã lưu lời mời nhưng gửi email thất bại (kiểm tra lại SMTP)"
        except Exception as e:
            logger.error(f"Lỗi khi gửi email lời mời: {e}")
            msg = "Đã lưu lời mời nhưng có lỗi khi gửi email"

        return InviteResponse(success=True, message=msg, invitation_id=invitation_id)

    def resend_invitation(
        self,
        baby_id: str,
        invitation_id: str,
        requester_uid: str,
        inviter_name: str = "Phụ huynh"
    ) -> InviteResponse:
        """Sinh token mới (vô hiệu hoá token cũ) và gửi lại email cho một lời mời đang pending."""
        require_role(baby_id, requester_uid, ADMIN)

        invitation = self.repo.get_invitation_by_id(invitation_id)
        if not invitation or invitation.get("baby_id") != baby_id:
            raise HTTPException(status_code=404, detail="Không tìm thấy lời mời.")
        if invitation.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Lời mời này đã được xử lý, không thể gửi lại.")

        token = _generate_invite_token()
        now = datetime.now(timezone.utc)
        self.repo.update_invitation(invitation_id, {
            "token_hash": _hash_token(token),
            "expires_at": (now + timedelta(days=INVITE_TTL_DAYS)).isoformat(),
        })

        try:
            baby = self.baby_repo.get(baby_id)
            baby_name = baby.name if baby else "Bé"
        except Exception:
            baby_name = "Bé"

        invite_link = f"{settings.FRONTEND_URL}/invite/{token}"
        sent_ok = self.email_svc.send_guardian_invitation_email(
            to_email=invitation["email"],
            guardian_name=invitation.get("name", ""),
            baby_name=baby_name,
            role=invitation.get("role", "GUARDIAN"),
            inviter_name=inviter_name,
            invite_link=invite_link
        )
        msg = "Đã gửi lại email mời thành công" if sent_ok else "Không thể gửi lại email (kiểm tra lại SMTP)"
        return InviteResponse(success=True, message=msg, invitation_id=invitation_id)

    # ─── Xoá / thu hồi ───────────────────────────────────────────────────────

    def remove_guardian(self, baby_id: str, guardian_id: str, requester_uid: str) -> MessageResponse:
        """
        Xóa một guardian đã tham gia, hoặc thu hồi một lời mời đang pending - dùng chung 1
        endpoint vì UI hiển thị cả 2 loại trong cùng danh sách với cùng nút xoá. Chỉ ADMIN mới
        được xoá/thu hồi.
        """
        require_role(baby_id, requester_uid, ADMIN)

        existing = self.repo.get_guardian_by_id(guardian_id)
        if existing:
            self.repo.delete_guardian(guardian_id)
            if existing.get("user_id"):
                self.repo.remove_from_baby_guardians_list(baby_id, existing["user_id"])
            return MessageResponse(success=True, message="Đã xoá người chăm sóc khỏi vòng kết nối gia đình.")

        invitation = self.repo.get_invitation_by_id(guardian_id)
        if invitation and invitation.get("baby_id") == baby_id:
            self.repo.delete_invitation(guardian_id)
            return MessageResponse(success=True, message="Đã thu hồi lời mời.")

        raise HTTPException(status_code=404, detail="Guardian not found")

    # ─── Trang xác nhận công khai (/invite/:token) ──────────────────────────

    def get_invitation_public(self, token: str) -> InvitationPublicInfo:
        """Trả thông tin công khai của lời mời để hiển thị trang xác nhận, không cần đăng nhập."""
        invitation = self.repo.get_invitation_by_token_hash(_hash_token(token))
        if not invitation:
            raise HTTPException(status_code=404, detail="Lời mời không tồn tại hoặc đã bị thu hồi.")

        status_value = self._resolve_status(invitation)

        try:
            baby = self.baby_repo.get(invitation["baby_id"])
        except Exception:
            baby = None

        return InvitationPublicInfo(
            baby_name=baby.name if baby else "Bé",
            baby_avatar_url=baby.avatar_url if baby else None,
            guardian_name=invitation.get("name", ""),
            invited_email=invitation.get("email", ""),
            role=invitation.get("role", "GUARDIAN"),
            status=status_value
        )

    def accept_invitation(self, token: str, current_user: UserRecord) -> MessageResponse:
        """
        Chấp nhận lời mời: bắt buộc email tài khoản đăng nhập khớp với email được mời, để
        tránh trường hợp ai có link mời cũng đăng nhập bằng tài khoản khác chiếm quyền truy
        cập hồ sơ bé thay vì đúng người được mời.
        """
        invitation = self.repo.get_invitation_by_token_hash(_hash_token(token))
        if not invitation:
            raise HTTPException(status_code=404, detail="Lời mời không tồn tại hoặc đã bị thu hồi.")

        status_value = self._resolve_status(invitation)
        if status_value == "accepted":
            return MessageResponse(success=True, message="Bạn đã tham gia chăm sóc bé này trước đó.")
        if status_value != "pending":
            raise HTTPException(status_code=400, detail="Lời mời không còn hiệu lực.")

        invited_email = (invitation.get("email") or "").strip().lower()
        current_email = (current_user.email or "").strip().lower()
        if not current_email or current_email != invited_email:
            raise HTTPException(
                status_code=403,
                detail=f"Email đăng nhập không khớp với email được mời ({invitation.get('email')}). "
                       f"Vui lòng đăng nhập hoặc đăng ký đúng tài khoản đã nhận lời mời."
            )

        baby_id = invitation["baby_id"]
        invitation_id = invitation["id"]

        self.repo.create_guardian({
            "baby_id": baby_id,
            "user_id": current_user.uid,
            "name": invitation.get("name") or current_user.name or current_user.email,
            "email": invitation.get("email"),
            "role": invitation.get("role", "GUARDIAN"),
            "status": "Synced"
        })
        self.repo.add_to_baby_guardians_list(baby_id, current_user.uid)
        self.repo.update_invitation(invitation_id, {
            "status": "accepted",
            "accepted_at": datetime.now(timezone.utc).isoformat(),
            "accepted_by": current_user.uid,
        })

        try:
            baby = self.baby_repo.get(baby_id)
            baby_name = baby.name if baby else "bé"
        except Exception:
            baby_name = "bé"

        invited_by = invitation.get("invited_by")
        if invited_by:
            notify_user(
                recipient_uid=invited_by,
                title="Lời mời đã được chấp nhận",
                message=f"{current_user.name or current_user.email} đã chấp nhận lời mời tham gia chăm sóc {baby_name}.",
                notif_type="system",
                baby_id=baby_id,
            )

        return MessageResponse(
            success=True,
            message="Chấp nhận lời mời thành công! Bạn đã chính thức tham gia chăm sóc bé."
        )

    def decline_invitation(self, token: str) -> MessageResponse:
        """Từ chối lời mời - không cần đăng nhập, và báo lại cho người mời qua chuông thông báo."""
        invitation = self.repo.get_invitation_by_token_hash(_hash_token(token))
        if not invitation:
            raise HTTPException(status_code=404, detail="Lời mời không tồn tại hoặc đã bị thu hồi.")

        status_value = self._resolve_status(invitation)
        if status_value == "declined":
            return MessageResponse(success=True, message="Bạn đã từ chối lời mời này trước đó.")
        if status_value != "pending":
            raise HTTPException(status_code=400, detail="Lời mời không còn hiệu lực để từ chối.")

        self.repo.update_invitation(invitation["id"], {
            "status": "declined",
            "declined_at": datetime.now(timezone.utc).isoformat(),
        })

        try:
            baby = self.baby_repo.get(invitation["baby_id"])
            baby_name = baby.name if baby else "bé"
        except Exception:
            baby_name = "bé"

        invited_by = invitation.get("invited_by")
        if invited_by:
            guardian_label = invitation.get("name") or invitation.get("email")
            notify_user(
                recipient_uid=invited_by,
                title="Lời mời đã bị từ chối",
                message=f"{guardian_label} đã từ chối lời mời tham gia chăm sóc {baby_name}.",
                notif_type="system",
                baby_id=invitation.get("baby_id"),
            )

        return MessageResponse(success=True, message="Đã từ chối lời mời.")

    def _resolve_status(self, invitation: dict) -> str:
        """Tự động chuyển pending -> expired nếu đã quá hạn (lazy expiry, không cần cron job)."""
        status_value = invitation.get("status", "pending")
        if status_value != "pending":
            return status_value

        expires_at = invitation.get("expires_at")
        if expires_at:
            try:
                if datetime.now(timezone.utc) >= datetime.fromisoformat(expires_at):
                    self.repo.update_invitation(invitation["id"], {"status": "expired"})
                    return "expired"
            except ValueError:
                pass
        return "pending"
