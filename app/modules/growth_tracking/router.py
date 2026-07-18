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


# Router mới hỗ trợ Frontend
from app.modules.growth_tracking.schemas import MeasurementCreate, MeasurementCreateResponse, MeasurementResponse, Percentiles, GrowthLogCreate
from typing import List, Optional

measurements_router = APIRouter(prefix="/growth/measurements", tags=["WHO Growth Charts"])

def map_status_to_percentile(status: Optional[str]) -> str:
    if not status:
        return "50th (Normal)"
    status_lower = status.lower()
    if "normal" in status_lower:
        return "50th (Normal)"
    elif "underweight" in status_lower or "stunted" in status_lower or "microcephaly" in status_lower:
        return "5th (Alert)"
    elif "overweight" in status_lower or "tall" in status_lower or "macrocephaly" in status_lower:
        return "95th (Alert)"
    return "50th (Normal)"

@measurements_router.get("", response_model=List[MeasurementResponse])
async def get_measurements(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy dữ liệu lịch sử số đo thể chất (Cân nặng, Chiều cao, Vòng đầu) của bé.
    """
    history = growth_service.get_growth_history(baby_id, user_id=current_user.uid)
    results = []
    for log in history:
        age_m = log.who_status.age_in_months if log.who_status else 0.0
        results.append(MeasurementResponse(
            id=log.id or "",
            age_months=age_m,
            weight=log.weight,
            height=log.height,
            head_circumference=log.head_circumference,
            date=log.logged_at[:10]  # Trả về YYYY-MM-DD
        ))
    return results

@measurements_router.post("", response_model=MeasurementCreateResponse)
async def add_measurement(
    m_in: MeasurementCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Thêm số đo tăng trưởng mới cho bé và trả về bách phân vị WHO.
    """
    log_in = GrowthLogCreate(
        height=m_in.height,
        weight=m_in.weight,
        head_circumference=m_in.head_circumference
    )
    result = growth_service.add_growth_log(m_in.baby_id, log_in, user_id=current_user.uid)
    
    w_p = map_status_to_percentile(result.who_status.weight_status if result.who_status else None)
    h_p = map_status_to_percentile(result.who_status.height_status if result.who_status else None)
    hc_p = map_status_to_percentile(result.who_status.head_circumference_status if result.who_status else None)
    
    return MeasurementCreateResponse(
        success=True,
        measurement_id=result.id or "",
        percentiles=Percentiles(
            weight_percentile=w_p,
            height_percentile=h_p,
            head_percentile=hc_p
        )
    )
