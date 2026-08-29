"""
Baby Schemas Module

Defines request and response schemas for baby profiles.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional


def _normalize_allergies(v):
    """
    Chuẩn hoá allergies về list[str], tương thích ngược với dữ liệu Firestore cũ
    lưu dạng chuỗi ngăn cách bởi dấu phẩy (trước khi field này chuyển sang list[str]).
    """
    if v is None:
        return v
    if isinstance(v, list):
        return [item.strip() for item in v if isinstance(item, str) and item.strip()]
    if isinstance(v, str):
        return [item.strip() for item in v.split(",") if item.strip()]
    return v


class BabyBase(BaseModel):
    name: str
    birth_date: str  # Định dạng YYYY-MM-DD
    gender: str = "unknown"  # boy, girl, unknown
    avatar_url: Optional[str] = None
    is_active: bool = True
    blood_type: Optional[str] = None  # A+, A-, B+, B-, AB+, AB-, O+, O-
    pediatrician_name: Optional[str] = None
    allergies: list[str] = Field(default_factory=list)  # Danh sách dị ứng chung (legacy)
    food_allergies: list[str] = Field(default_factory=list)  # Dị ứng thực phẩm & sữa
    medication_allergies: list[str] = Field(default_factory=list)  # Dị ứng thuốc & dược chất

    @field_validator("allergies", "food_allergies", "medication_allergies", mode="before")
    @classmethod
    def validate_allergies(cls, v):
        normalized = _normalize_allergies(v)
        return normalized if normalized is not None else []


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
    allergies: Optional[list[str]] = None
    food_allergies: Optional[list[str]] = None
    medication_allergies: Optional[list[str]] = None

    @field_validator("allergies", "food_allergies", "medication_allergies", mode="before")
    @classmethod
    def validate_allergies(cls, v):
        return _normalize_allergies(v)


class BabyResponse(BaseModel):
    id: Optional[str] = None
    name: str
    birth_date: str  # Định dạng YYYY-MM-DD
    gender: str = "unknown"  # boy, girl, unknown
    avatar_url: Optional[str] = None
    is_active: bool = True
    blood_type: Optional[str] = None
    pediatrician_name: Optional[str] = None
    allergies: list[str] = Field(default_factory=list)
    food_allergies: list[str] = Field(default_factory=list)
    medication_allergies: list[str] = Field(default_factory=list)
    guardians: list[str] = []
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @field_validator("allergies", "food_allergies", "medication_allergies", mode="before")
    @classmethod
    def validate_allergies(cls, v):
        normalized = _normalize_allergies(v)
        return normalized if normalized is not None else []


class AvatarUploadResponse(BaseModel):
    avatar_url: str

