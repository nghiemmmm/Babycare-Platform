from pydantic import BaseModel
from typing import Optional

class GuardianResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    status: str

class GuardianInvite(BaseModel):
    name: str
    email: str
    role: str

class InviteResponse(BaseModel):
    success: bool
    message: str
    invitation_id: str

class MessageResponse(BaseModel):
    success: bool
    message: str
