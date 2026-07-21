"""
Baby Schemas Module

Defines request and response schemas for baby profiles.
"""
from pydantic import BaseModel
from typing import Optional

class BabyBase(BaseModel):
    name: str
    birth_date: str  # Định dạng YYYY-MM-DD
    gender: str = "unknown"  # boy, girl, unknown
    avatar_url: Optional[str] = None
    is_active: bool = True
    blood_type: Optional[str] = None  # A+, A-, B+, B-, AB+, AB-, O+, O-
    pediatrician_name: Optional[str] = None
    allergies: Optional[str] = None  # Chuỗi tự do, ngăn cách bởi dấu phẩy


class BabyCreate(BabyBase):
    pass


class BabyUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    guardians: Optional[list[str]] = None
    blood_type: Optional[str] = None
    pediatrician_name: Optional[str] = None
    allergies: Optional[str] = None


class BabyResponse(BabyBase):
    id: Optional[str] = None
    guardians: list[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AvatarUploadResponse(BaseModel):
    avatar_url: str
