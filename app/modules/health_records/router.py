"""
Health Records Router Module

Defines HTTP API endpoints for managing baby medical history and symptoms.
"""
from fastapi import APIRouter, Depends, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.health_records.schemas import HealthRecordCreate, HealthRecordResponse
from app.modules.health_records.service import HealthRecordService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Health Records"])
health_service = HealthRecordService()

@router.post("/{baby_id}/health-records", response_model=HealthRecordResponse, status_code=status.HTTP_201_CREATED)
async def add_baby_health_record(
    baby_id: str,
    record_in: HealthRecordCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Thêm một bệnh án mới cho bé (Yêu cầu quyền giám hộ).
    """
    return health_service.add_record(baby_id, record_in, user_id=current_user.uid)

@router.get("/{baby_id}/health-records", response_model=list[HealthRecordResponse])
async def get_baby_health_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử bệnh án, triệu chứng của bé (Yêu cầu quyền giám hộ).
    """
    return health_service.get_history(baby_id, user_id=current_user.uid)

@router.patch("/{baby_id}/health-records/{record_id}", response_model=HealthRecordResponse)
async def update_baby_health_record(
    baby_id: str,
    record_id: str,
    update_in: HealthRecordUpdate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cập nhật trạng thái hoặc thông tin bệnh án của bé.
    """
    update_data = {k: v for k, v in update_in.model_dump().items() if v is not None}
    return health_service.update_record(baby_id, record_id, update_data, user_id=current_user.uid)


@router.delete("/{baby_id}/health-records/{record_id}", response_model=Message)
async def delete_baby_health_record(
    baby_id: str,
    record_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi bệnh án (Yêu cầu quyền giám hộ).
    """
    health_service.delete_record(baby_id, record_id, user_id=current_user.uid)
    return Message(message="Xóa bản ghi bệnh án thành công")

