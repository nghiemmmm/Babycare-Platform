"""
Growth Tracking Router Module

Defines HTTP API endpoints for logging and viewing baby growth logs.
"""
from fastapi import APIRouter, Depends, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.growth_tracking.schemas import GrowthLogCreate, GrowthLogResponse
from app.modules.growth_tracking.service import GrowthTrackingService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Growth Tracking"])
growth_service = GrowthTrackingService()

@router.post("/{baby_id}/growth", response_model=GrowthLogResponse, status_code=status.HTTP_201_CREATED)
async def add_baby_growth_log(
    baby_id: str,
    log_in: GrowthLogCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận một bản ghi cân nặng/chiều cao mới cho bé (Yêu cầu quyền giám hộ).
    """
    return growth_service.add_growth_log(baby_id, log_in, user_id=current_user.uid)

@router.get("/{baby_id}/growth", response_model=list[GrowthLogResponse])
async def get_baby_growth_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử tăng trưởng của bé (Yêu cầu quyền giám hộ).
    """
    return growth_service.get_growth_history(baby_id, user_id=current_user.uid)

@router.delete("/{baby_id}/growth/{log_id}", response_model=Message)
async def delete_baby_growth_log(
    baby_id: str,
    log_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi nhật ký tăng trưởng (Yêu cầu quyền giám hộ).
    """
    growth_service.delete_growth_log(baby_id, log_id, user_id=current_user.uid)
    return Message(message="Xóa bản ghi nhật ký thành công")
