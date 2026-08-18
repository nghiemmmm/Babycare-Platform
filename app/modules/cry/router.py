"""
AI Cry Tracking & Prediction Router Module

Defines HTTP API endpoints for uploading cry recordings and reviewing AI predictions.
"""
from fastapi import APIRouter, Depends, status, UploadFile, File
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.cry.schemas import CryLogResponse
from app.modules.cry.service import CryService
from app.shared.schemas import Message
from app.shared.concurrency import run_in_threadpool

router = APIRouter(prefix="/babies", tags=["AI Cry Detection"])
cry_service = CryService()

@router.post("/{baby_id}/cry-prediction", response_model=CryLogResponse, status_code=status.HTTP_201_CREATED)
async def predict_baby_cry(
    baby_id: str,
    audio_file: UploadFile = File(..., description="Tệp ghi âm tiếng khóc (.wav, .mp3)"),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Tải tệp ghi âm tiếng khóc lên để phân tích nguyên nhân khóc và kích hoạt tự động âm thanh dỗ bé (Yêu cầu quyền giám hộ).
    """
    return await run_in_threadpool(cry_service.predict_cry, baby_id, audio_file, user_id=current_user.uid)

@router.get("/{baby_id}/cry-prediction", response_model=list[CryLogResponse])
async def get_cry_prediction_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy lịch sử dự đoán tiếng khóc của bé (Yêu cầu quyền giám hộ).
    """
    return cry_service.get_cry_history(baby_id, user_id=current_user.uid)

from typing import Union
from app.modules.cry.schemas import CryLogResponse, CryFeedbackUpdate

@router.patch("/{baby_id}/cry-prediction/{log_id}/feedback", response_model=CryLogResponse)
async def update_cry_feedback(
    baby_id: str,
    log_id: str,
    feedback: Union[CryFeedbackUpdate, bool],
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cập nhật phản hồi thực tế của phụ huynh và kết quả can thiệp để đánh giá độ chính xác của AI (Yêu cầu quyền giám hộ).
    """
    return cry_service.update_parent_feedback(baby_id, log_id, feedback, user_id=current_user.uid)


@router.delete("/{baby_id}/cry-prediction/{log_id}", response_model=Message)
async def delete_cry_log(
    baby_id: str,
    log_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi lịch sử tiếng khóc của bé (Yêu cầu quyền giám hộ).
    """
    cry_service.delete_cry_log(baby_id, log_id, user_id=current_user.uid)
    return Message(message="Xóa bản ghi tiếng khóc thành công")
