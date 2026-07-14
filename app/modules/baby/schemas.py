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


class BabyCreate(BabyBase):
    pass


class BabyUpdate(BaseModel):
    name: Optional[str] = None
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    guardians: Optional[list[str]] = None


class BabyResponse(BabyBase):
    id: Optional[str] = None
    guardians: list[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
