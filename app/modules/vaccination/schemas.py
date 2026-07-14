"""
Vaccination Schemas Module

Defines request and response schemas for tracking baby vaccination schedule.
"""
from pydantic import BaseModel
from typing import Optional

class VaccinationUpdate(BaseModel):
    status: str  # scheduled, completed, overdue
    administered_date: Optional[str] = None  # Định dạng YYYY-MM-DD
    notes: Optional[str] = None


class VaccinationResponse(BaseModel):
    id: Optional[str] = None  # Document ID (trùng khớp với vaccine_code)
    vaccine_code: str
    vaccine_name: str
    scheduled_date: str
    administered_date: Optional[str] = None
    status: str = "scheduled"
    notes: Optional[str] = None
