"""
Vaccination Router Module

Defines HTTP API endpoints for managing baby vaccination schedule and history.
"""
from fastapi import APIRouter, Depends
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.vaccination.schemas import VaccinationUpdate, VaccinationResponse
from app.modules.vaccination.service import VaccinationService

router = APIRouter(prefix="/babies", tags=["Vaccination"])
vaccination_service = VaccinationService()

@router.get("/{baby_id}/vaccinations", response_model=list[VaccinationResponse])
async def get_baby_vaccine_schedule(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch trình tiêm chủng dự kiến và thực tế của bé (Yêu cầu quyền giám hộ).
    """
    return vaccination_service.get_baby_vaccinations(baby_id, user_id=current_user.uid)

@router.put("/{baby_id}/vaccinations/{vaccine_code}", response_model=VaccinationResponse)
async def update_baby_vaccine_status(
    baby_id: str,
    vaccine_code: str,
    vaccination_update: VaccinationUpdate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cập nhật trạng thái của một mũi tiêm (Đã tiêm / Quá hạn / Thêm ghi chú) (Yêu cầu quyền giám hộ).
    """
    return vaccination_service.update_vaccination_status(
        baby_id, vaccine_code, vaccination_update, user_id=current_user.uid
    )
