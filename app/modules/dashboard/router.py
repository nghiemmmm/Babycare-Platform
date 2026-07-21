"""
Dashboard Router - Chỉ nhận HTTP request và ủy quyền cho DashboardAggregator.
Một endpoint duy nhất: GET /api/v1/dashboard
"""
from fastapi import APIRouter, Depends, Query

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.dashboard.aggregator import DashboardAggregator
from app.modules.dashboard.schemas import DashboardResponse

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
