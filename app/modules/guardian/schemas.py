from pydantic import BaseModel
from typing import Literal, Optional

GuardianRole = Literal["ADMIN", "GUARDIAN", "VIEWER"]


class GuardianResponse(BaseModel):
    id: str
    name: str
    email: str
    role: GuardianRole
    status: str  # "Synced" (đã tham gia) | "Invited" (đang chờ phản hồi)


class GuardianInvite(BaseModel):
    name: str
    email: str
    role: GuardianRole


class InviteResponse(BaseModel):
    success: bool
    message: str
    invitation_id: str


class MessageResponse(BaseModel):
    success: bool
    message: str


class InvitationPublicInfo(BaseModel):
    """
    Thông tin công khai của một lời mời, phục vụ trang xác nhận /invite/:token mà KHÔNG cần
    đăng nhập - chỉ lộ đúng những gì cần để người được mời quyết định chấp nhận/từ chối.
    """
    baby_name: str
    baby_avatar_url: Optional[str] = None
    guardian_name: str
    invited_email: str
    role: GuardianRole
    status: str  # "pending" | "accepted" | "declined" | "expired"
