"""
Guardian Router - Chỉ chịu trách nhiệm nhận HTTP request và trả về HTTP response.
Toàn bộ business logic được ủy quyền cho GuardianService.
"""
from fastapi import APIRouter, Depends, Query
from typing import List

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.baby.service import BabyService
from app.modules.guardian.service import GuardianService
from app.modules.guardian.schemas import (
    GuardianResponse,
    GuardianInvite,
    InvitationPublicInfo,
    InviteResponse,
    MessageResponse
)

router = APIRouter(prefix="/guardians", tags=["Guardians Circle"])

baby_service = BabyService()
guardian_service = GuardianService()


@router.get("", response_model=List[GuardianResponse])
async def list_guardians(
    baby_id: str = Query(..., description="ID of the active baby"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Lấy danh sách những người chăm sóc (Caregivers Circle) của bé."""
    baby_service.get_baby_by_id(baby_id, current_user.uid)
    return guardian_service.list_guardians(
        baby_id=baby_id,
        fallback_name=current_user.name or "Elena",
        fallback_email=current_user.email or "mom@family.com",
        user_id=current_user.uid
    )


@router.post("/invite", response_model=InviteResponse)
async def invite_guardian(
    invite_in: GuardianInvite,
    baby_id: str = Query(..., description="ID of the active baby"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Mời một người chăm sóc mới tham gia vòng tròn gia đình chăm sóc bé (chỉ ADMIN)."""
    baby_service.get_baby_by_id(baby_id, current_user.uid)
    return guardian_service.invite_guardian(
        baby_id=baby_id,
        name=invite_in.name,
        email=invite_in.email,
        role=invite_in.role,
        invited_by_uid=current_user.uid,
        inviter_name=current_user.name or "Phụ huynh"
    )


@router.post("/{guardian_id}/resend", response_model=InviteResponse)
async def resend_guardian_invitation(
    guardian_id: str,
    baby_id: str = Query(..., description="ID of the active baby"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Gửi lại email mời cho một lời mời đang chờ phản hồi (chỉ ADMIN)."""
    baby_service.get_baby_by_id(baby_id, current_user.uid)
    return guardian_service.resend_invitation(
        baby_id=baby_id,
        invitation_id=guardian_id,
        requester_uid=current_user.uid,
        inviter_name=current_user.name or "Phụ huynh"
    )


@router.delete("/{guardian_id}", response_model=MessageResponse)
async def delete_guardian(
    guardian_id: str,
    baby_id: str = Query(..., description="ID of the active baby"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Xóa quyền truy cập của một người chăm sóc, hoặc thu hồi một lời mời đang chờ (chỉ ADMIN)."""
    baby_service.get_baby_by_id(baby_id, current_user.uid)
    return guardian_service.remove_guardian(baby_id=baby_id, guardian_id=guardian_id, requester_uid=current_user.uid)


@router.get("/invite/{token}", response_model=InvitationPublicInfo)
async def get_invitation_public(token: str):
    """
    Thông tin công khai của một lời mời - phục vụ trang xác nhận /invite/:token trên frontend,
    KHÔNG yêu cầu đăng nhập (người được mời có thể chưa có tài khoản).
    """
    return guardian_service.get_invitation_public(token)


@router.post("/invite/{token}/accept", response_model=MessageResponse)
async def accept_guardian_invitation(
    token: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Chấp nhận lời mời - yêu cầu đăng nhập, vì hệ thống cần biết chấp nhận gắn với user nào.
    Email tài khoản đăng nhập phải khớp với email được mời.
    """
    return guardian_service.accept_invitation(token=token, current_user=current_user)


@router.post("/invite/{token}/decline", response_model=MessageResponse)
async def decline_guardian_invitation(token: str):
    """Từ chối lời mời - không yêu cầu đăng nhập, vì từ chối không cần gắn với tài khoản nào."""
    return guardian_service.decline_invitation(token=token)
