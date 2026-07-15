"""
Medication Tracking Router Module

Defines HTTP API endpoints for logging and viewing baby medication history.
"""
from fastapi import APIRouter, Depends, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.medication.schemas import MedicationLogCreate, MedicationLogResponse
from app.modules.medication.service import MedicationService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Medication Tracking"])
med_service = MedicationService()

@router.post("/{baby_id}/medication", response_model=MedicationLogResponse, status_code=status.HTTP_201_CREATED)
async def add_medication_log(
    baby_id: str,
    log_in: MedicationLogCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận một bản ghi nhật ký dùng thuốc/vitamin mới cho bé (Yêu cầu quyền giám hộ).
    """
    return med_service.add_medication_log(baby_id, log_in, user_id=current_user.uid)

@router.get("/{baby_id}/medication", response_model=list[MedicationLogResponse])
async def get_medication_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử dùng thuốc/vitamin của bé (Yêu cầu quyền giám hộ).
    """
    return med_service.get_medication_history(baby_id, user_id=current_user.uid)

@router.delete("/{baby_id}/medication/{log_id}", response_model=Message)
async def delete_medication_log(
    baby_id: str,
    log_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi nhật ký dùng thuốc/vitamin của bé (Yêu cầu quyền giám hộ).
    """
    med_service.delete_medication_log(baby_id, log_id, user_id=current_user.uid)
    return Message(message="Xóa nhật ký dùng thuốc thành công")
