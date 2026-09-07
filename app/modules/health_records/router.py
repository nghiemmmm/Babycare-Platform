"""
Health Records Router Module

Defines HTTP API endpoints for managing baby health episodes,
time-series health events, and legacy medical records.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.health_records.schemas import (
    HealthEpisodeCreate,
    HealthEpisodeResponse,
    HealthEpisodeDetailResponse,
    HealthEventCreate,
    HealthEventResponse,
    HealthRecordCreate,
    HealthRecordResponse,
    HealthRecordUpdate
)
from app.modules.health_records.service import HealthRecordService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Health Records & Episodes"])
health_service = HealthRecordService()


# ============================================================================
# 1. HEALTH EPISODES & TIMELINE (Đợt theo dõi sức khỏe & Sự kiện theo giờ)
# ============================================================================

@router.post("/{baby_id}/health-episodes", response_model=HealthEpisodeDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_health_episode(
    baby_id: str,
    episode_in: HealthEpisodeCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Khởi tạo đợt theo dõi sức khỏe mới cho bé (Hô hấp, Tiêu hóa, Da liễu, Mọc răng, Sốt...).
    """
    user_name = current_user.name or "Phụ huynh"
    return health_service.create_episode(baby_id, episode_in, user_id=current_user.uid, user_name=user_name)


@router.get("/{baby_id}/health-episodes/active", response_model=Optional[HealthEpisodeDetailResponse])
async def get_active_health_episode(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy đợt bệnh đang theo dõi hiện tại của bé kèm toàn bộ dòng thời gian sự kiện.
    """
    return health_service.get_active_episode(baby_id, user_id=current_user.uid)


@router.get("/{baby_id}/health-episodes", response_model=List[HealthEpisodeResponse])
async def list_health_episodes(
    baby_id: str,
    status_filter: Optional[str] = Query(None, description="Lọc theo trạng thái: active | resolved"),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy danh sách các đợt theo dõi sức khỏe của bé.
    """
    return health_service.list_episodes(baby_id, user_id=current_user.uid, status_filter=status_filter)


@router.get("/{baby_id}/health-episodes/{episode_id}", response_model=HealthEpisodeDetailResponse)
async def get_health_episode_detail(
    baby_id: str,
    episode_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy chi tiết một đợt theo dõi sức khỏe kèm toàn bộ sự kiện theo dòng thời gian.
    """
    return health_service.get_episode_detail(baby_id, episode_id, user_id=current_user.uid)


@router.post("/{baby_id}/health-episodes/{episode_id}/events", response_model=HealthEventResponse, status_code=status.HTTP_201_CREATED)
async def add_health_event_to_episode(
    baby_id: str,
    episode_id: str,
    event_in: HealthEventCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận nhanh một sự kiện vào đợt theo dõi (đo nhiệt độ, cữ ho, cữ đi tiêu, rửa mũi, uống thuốc...).
    """
    user_name = current_user.name or "Phụ huynh"
    return health_service.add_event(baby_id, episode_id, event_in, user_id=current_user.uid, user_name=user_name)


@router.patch("/{baby_id}/health-episodes/{episode_id}/resolve", response_model=HealthEpisodeResponse)
async def resolve_health_episode(
    baby_id: str,
    episode_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Đánh dấu kết thúc đợt bệnh (Bé đã khỏi bệnh hoàn toàn).
    """
    user_name = current_user.name or "Phụ huynh"
    return health_service.resolve_episode(baby_id, episode_id, user_id=current_user.uid, user_name=user_name)


# ============================================================================
# 2. LEGACY HEALTH RECORDS (Tương thích ngược 100%)
# ============================================================================

@router.post("/{baby_id}/health-records", response_model=HealthRecordResponse, status_code=status.HTTP_201_CREATED)
async def add_baby_health_record(
    baby_id: str,
    record_in: HealthRecordCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Thêm một bệnh án mới cho bé (API cũ).
    """
    return health_service.add_record(baby_id, record_in, user_id=current_user.uid)


@router.get("/{baby_id}/health-records", response_model=list[HealthRecordResponse])
async def get_baby_health_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử bệnh án, triệu chứng của bé (API cũ).
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
    Cập nhật trạng thái hoặc thông tin bệnh án của bé (API cũ).
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
    Xóa một bản ghi bệnh án (API cũ).
    """
    health_service.delete_record(baby_id, record_id, user_id=current_user.uid)
    return Message(message="Xóa bản ghi bệnh án thành công")
