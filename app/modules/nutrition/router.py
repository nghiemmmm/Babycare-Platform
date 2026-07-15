"""
Solid Food Tracking Router Module

Defines HTTP API endpoints for logging and viewing baby solid food history.
"""
from fastapi import APIRouter, Depends, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.nutrition.schemas import SolidFoodLogCreate, SolidFoodLogResponse
from app.modules.nutrition.service import SolidFoodService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Solid Food Tracking"])
solid_food_service = SolidFoodService()

@router.post("/{baby_id}/nutrition/solid", response_model=SolidFoodLogResponse, status_code=status.HTTP_201_CREATED)
async def add_solid_food_log(
    baby_id: str,
    log_in: SolidFoodLogCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận một bản ghi nhật ký ăn dặm mới cho bé (Yêu cầu quyền giám hộ).
    """
    return solid_food_service.add_solid_food_log(baby_id, log_in, user_id=current_user.uid)

@router.get("/{baby_id}/nutrition/solid", response_model=list[SolidFoodLogResponse])
async def get_solid_food_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử ăn dặm của bé (Yêu cầu quyền giám hộ).
    """
    return solid_food_service.get_solid_food_history(baby_id, user_id=current_user.uid)

@router.delete("/{baby_id}/nutrition/solid/{log_id}", response_model=Message)
async def delete_solid_food_log(
    baby_id: str,
    log_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi nhật ký ăn dặm của bé (Yêu cầu quyền giám hộ).
    """
    solid_food_service.delete_solid_food_log(baby_id, log_id, user_id=current_user.uid)
    return Message(message="Xóa nhật ký ăn dặm thành công")
