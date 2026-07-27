from pydantic import BaseModel
from typing import Optional, List, Any

# Existing legacy support schemas
class ChatRequest(BaseModel):
    message: str
    baby_id: Optional[str] = None
    thread_id: str

class ChatResponse(BaseModel):
    response: str
    next_step: Optional[str] = None

# New Frontend API schemas
class ThreadResponse(BaseModel):
    id: str
    title: str
    last_updated: str
    baby_id: Optional[str] = None
    last_message_preview: Optional[str] = None

class ThreadCreateRequest(BaseModel):
    baby_id: str

class ThreadCreateResponse(BaseModel):
    thread_id: str
    title: str

class MessageCreateRequest(BaseModel):
    content: str
    type: str = "text"
    baby_id: str

class Citation(BaseModel):
    title: str
    uri: str

class ExtractedLog(BaseModel):
    type: str
    title: str
    detail: str
    value: Any
    time: str

class MessageResponseDetails(BaseModel):
    content: str
    citations: List[Citation] = []

class MessageCreateResponse(BaseModel):
    ai_response: MessageResponseDetails
    extracted_logs: List[ExtractedLog] = []

class SleepTimerRequest(BaseModel):
    baby_id: str
    action: str  # "start" / "stop"

class SleepTimerResponse(BaseModel):
    success: bool
    status: str
    start_time: str

class ChatMessageResponse(BaseModel):
    id: str
    role: str  # "user" / "assistant"
    content: str
    timestamp: str

class VoiceExtractRequest(BaseModel):
    transcript: str
    baby_id: Optional[str] = None

class VoiceExtractResponse(BaseModel):
    intent: str  # "feeding" | "medication" | "growth" | "diaper" | "sleep" | "unknown"
    extracted_data: dict
    confidence_message: str

