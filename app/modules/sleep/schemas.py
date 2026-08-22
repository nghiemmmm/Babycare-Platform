"""
Sleep Schemas Module
====================
Defines Pydantic data models for baby sleep logs and timers.
"""
from typing import Optional
from pydantic import BaseModel, Field


class SleepLogCreate(BaseModel):
    action: str = Field("wake", description="start_sleep | wake | nap")
    duration_minutes: Optional[int] = Field(None, description="Thời lượng giấc ngủ tính bằng phút")
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None
    logged_at: Optional[str] = None


class SleepLogResponse(BaseModel):
    id: Optional[str] = None
    action: str = "wake"
    duration_minutes: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    notes: Optional[str] = None
    logged_at: str


class SleepTimerRequest(BaseModel):
    baby_id: str
    action: str  # "start" | "stop" | "status"


class SleepTimerResponse(BaseModel):
    baby_id: str
    is_running: bool
    started_at: Optional[str] = None
    elapsed_seconds: int = 0
    message: str
