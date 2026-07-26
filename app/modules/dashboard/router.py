"""
Dashboard Router - Chỉ nhận HTTP request và ủy quyền cho DashboardAggregator.
Một endpoint duy nhất: GET /api/v1/dashboard
"""
from typing import List
from fastapi import APIRouter, Depends, Query, Path

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.dashboard.aggregator import DashboardAggregator
from app.modules.dashboard.schemas import DashboardResponse, NotificationResponse

router = APIRouter(tags=["Dashboard"])

aggregator = DashboardAggregator()


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    baby_id: str = Query(..., description="ID of the active baby"),
    current_user: UserRecord = Depends(get_current_user),
):
    """
    Aggregated Dashboard — Frontend chỉ cần gọi 1 endpoint này để lấy
    toàn bộ dữ liệu hiển thị: sữa, ngủ, tã, thuốc, tăng trưởng, AI tip,
    và activity stream.
    """
    return aggregator.build(baby_id=baby_id, user_id=current_user.uid)


@router.get("/dashboard/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    baby_id: str = Query(..., description="ID of the active baby"),
    current_user: UserRecord = Depends(get_current_user),
):
    """
    Lấy danh sách thông báo và cảnh báo mới nhất của bé từ Firestore.
    """
    return aggregator.get_notifications(baby_id=baby_id, user_id=current_user.uid)


@router.post("/dashboard/notifications/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: str = Path(..., description="Notification ID to mark as read"),
    current_user: UserRecord = Depends(get_current_user),
):
    """
    Đánh dấu thông báo là đã đọc trong Firestore.
    """
    success = aggregator.mark_notification_as_read(notification_id=notification_id)
    return {"success": success, "notification_id": notification_id}
