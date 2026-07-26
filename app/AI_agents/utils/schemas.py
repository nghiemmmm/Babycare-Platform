from pydantic import BaseModel, Field
from typing import Optional, List

class FeedingLogSchema(BaseModel):
    food_name: str = Field(..., min_length=1, description="Name of the food/milk.")
    amount_g: float = Field(..., gt=0, description="Amount of food in grams or milliliters.")
    reaction: Optional[str] = Field(None, description="Optional reaction of the baby.")
    notes: Optional[str] = Field(None, description="Optional additional notes.")
    logged_at: Optional[str] = Field(None, description="ISO timestamp of the event.")

class MedicationLogSchema(BaseModel):
    medication_name: str = Field(..., min_length=1, description="Name of the medication.")
    dosage: str = Field(..., min_length=1, description="Dosage details (e.g. 150mg, 2 drops).")
    prescribed_by: Optional[str] = Field(None, description="Optional prescribing doctor.")
    notes: Optional[str] = Field(None, description="Optional additional notes.")
    logged_at: Optional[str] = Field(None, description="ISO timestamp of the event.")

class SymptomLogSchema(BaseModel):
    symptoms: List[str] = Field(..., min_length=1, description="List of symptoms recorded.")
    diagnosis: Optional[str] = Field(None, description="Optional diagnosis.")
    treatment: Optional[str] = Field(None, description="Optional treatment notes.")
    doctor_name: Optional[str] = Field(None, description="Optional doctor name.")
    notes: Optional[str] = Field(None, description="Optional additional notes.")
    recorded_at: Optional[str] = Field(None, description="ISO timestamp of the event.")

class GrowthLogSchema(BaseModel):
    height: float = Field(..., gt=0, description="Height in cm.")
    weight: float = Field(..., gt=0, description="Weight in kg.")
    head_circumference: Optional[float] = Field(None, gt=0, description="Head circumference in cm.")
