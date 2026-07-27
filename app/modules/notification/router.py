"""
Notification Router - thông báo gắn với người dùng hiện tại, không lọc theo baby_id đang
chọn (khác app/modules/dashboard/router.py chỉ trả thông báo của một bé cụ thể).
"""
from typing import List
from fastapi import APIRouter, Depends, Path

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.dashboard.schemas import NotificationResponse
from app.modules.notification.service import get_notifications_for_user, mark_as_read

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/me", response_model=List[NotificationResponse])
async def get_my_notifications(current_user: UserRecord = Depends(get_current_user)):
    """Lấy thông báo của người dùng hiện tại (vd. kết quả lời mời guardian), không phụ thuộc
    bé nào đang được chọn trên UI."""
    return get_notifications_for_user(current_user.uid)


@router.post("/{notification_id}/read")
async def mark_my_notification_as_read(
    notification_id: str = Path(...),
    current_user: UserRecord = Depends(get_current_user),
):
    """Đánh dấu một thông báo là đã đọc."""
    success = mark_as_read(notification_id)
    return {"success": success, "notification_id": notification_id}
