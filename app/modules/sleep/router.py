"""
Sleep Router Module
===================
API Endpoints cho quản lý giấc ngủ bé và dự đoán Wake Window cá nhân hóa:
- GET  /api/v1/babies/{baby_id}/sleep/next-wake-window (Dự đoán Sweet Spot)
- POST /api/v1/babies/{baby_id}/sleep/records (Ghi nhận giấc ngủ)
- GET  /api/v1/babies/{baby_id}/sleep/records (Lịch sử giấc ngủ)
- POST /api/v1/babies/{baby_id}/sleep/timer (Hẹn giờ giấc ngủ: start | stop | status)
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.sleep.service import SleepService
from app.modules.sleep.schemas import (
    SleepLogCreate,
    SleepLogResponse,
    SleepTimerRequest,
    SleepTimerResponse,
)
from app.modules.sleep.wake_window_schemas import WakeWindowPredictionResponse

sleep_router = APIRouter(prefix="/babies/{baby_id}/sleep", tags=["Sleep & Wake Window"])
sleep_service = SleepService()


@sleep_router.get(
    "/next-wake-window",
    response_model=WakeWindowPredictionResponse,
    summary="Dự đoán Cửa sổ thức (Wake Window) và Điểm rơi giấc ngủ tối ưu (Sweet Spot)",
    description="Ứng dụng Global LightGBM + Feature Engineering 5 ngày + Expert Safety Guardrails + LLM Anomaly Reasoner bám sát Patent US 20250292903.",
)
async def predict_next_wake_window(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user),
):
    user_id = current_user.uid
    return await sleep_service.predict_next_wake_window(baby_id=baby_id, user_id=user_id)


@sleep_router.post(
    "/records",
    response_model=SleepLogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ghi nhận nhật ký giấc ngủ mới",
)
def add_sleep_record(
    baby_id: str,
    log_in: SleepLogCreate,
    current_user: UserRecord = Depends(get_current_user),
):
    user_id = current_user.uid
    return sleep_service.add_sleep_log(baby_id, log_in, user_id)


@sleep_router.get(
    "/records",
    response_model=List[SleepLogResponse],
    summary="Lấy lịch sử giấc ngủ của bé",
)
def get_sleep_history(
    baby_id: str,
    limit: int = Query(50, ge=1, le=100),
    current_user: UserRecord = Depends(get_current_user),
):
    user_id = current_user.uid
    return sleep_service.get_sleep_history(baby_id, user_id, limit=limit)


@sleep_router.post(
    "/timer",
    response_model=SleepTimerResponse,
    summary="Quản lý bộ hẹn giờ giấc ngủ (start | stop | status)",
)
def handle_sleep_timer(
    baby_id: str,
    timer_req: SleepTimerRequest,
    current_user: UserRecord = Depends(get_current_user),
):
    user_id = current_user.uid
    return sleep_service.handle_sleep_timer(baby_id, timer_req.action, user_id)
