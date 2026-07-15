"""
AI Cry Tracking Schemas Module

Defines request and response schemas for tracking baby cry logs and AI sound conditioning.
"""
from pydantic import BaseModel, Field
from typing import Optional

class CryLogBase(BaseModel):
    logged_at: str = Field(..., description="Thời điểm bé khóc (ISO 8601)")
    audio_url: str = Field(..., description="Đường dẫn lưu trữ tệp ghi âm tiếng khóc (.wav, .mp3) trên Firebase Storage")
    
    # Kết quả chẩn đoán từ AI
    prediction: str = Field(..., description="Dự đoán của AI: hungry, tired, pain, diaper, discomfort")
    confidence: float = Field(..., description="Độ tin cậy của dự đoán (từ 0.0 đến 1.0)")
    
    # Phản hồi từ phụ huynh & Kích hoạt âm thanh vỗ về tự động
    feedback_accurate: Optional[bool] = Field(None, description="Đánh giá từ phụ huynh xem AI đoán đúng hay sai")
    sound_conditioned: bool = Field(False, description="Đã tự động kích hoạt âm thanh vỗ về hay chưa")
    sound_played: Optional[str] = Field(None, description="Tên âm thanh/nhạc đã phát")
    notes: Optional[str] = Field(None, description="Ghi chú bổ sung")

class CryLogCreate(CryLogBase):
    pass

class CryLogResponse(CryLogBase):
    id: Optional[str] = None
