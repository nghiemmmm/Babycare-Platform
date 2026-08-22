from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class TaskTypeEnum(str, Enum):
    FEEDING = "feeding"
    MEDICATION = "medication"
    SLEEP = "sleep"
    HYGIENE = "hygiene"
    ACTIVITY = "activity"
    HEALTH_CHECK = "health_check"
    CUSTOM = "custom"


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    DUE = "due"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    OVERDUE = "overdue"
    ESCALATED = "escalated"


class PriorityEnum(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# ─── 1. HANDOVER NOTES SCHEMAS ───────────────────────────────────────────────

class HandoverNoteCreate(BaseModel):
    baby_id: str
    content: str
    date: Optional[str] = None  # YYYY-MM-DD
    voice_note_url: Optional[str] = None
    photo_urls: Optional[List[str]] = Field(default_factory=list)


class HandoverNoteResponse(BaseModel):
    id: str
    baby_id: str
    date: str
    created_by: str
    author_name: str
    content: str
    voice_note_url: Optional[str] = None
    photo_urls: List[str] = Field(default_factory=list)
    acknowledged_by: List[str] = Field(default_factory=list)
    created_at: str


# ─── 2. CARE TASK SCHEMAS ───────────────────────────────────────────────────

class CareTaskCreate(BaseModel):
    baby_id: str
    task_type: TaskTypeEnum = TaskTypeEnum.CUSTOM
    title: str
    scheduled_time: str  # ISO string or HH:MM
    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None
    backup_assigned_to: Optional[str] = None
    backup_assigned_name: Optional[str] = None
    instructions: Optional[str] = None
    target_value: Optional[Dict[str, Any]] = None  # {"amount": 150, "unit": "ml"}
    priority: PriorityEnum = PriorityEnum.NORMAL
    is_recurring: bool = False


class CareTaskUpdate(BaseModel):
    title: Optional[str] = None
    scheduled_time: Optional[str] = None
    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None
    backup_assigned_to: Optional[str] = None
    backup_assigned_name: Optional[str] = None
    instructions: Optional[str] = None
    target_value: Optional[Dict[str, Any]] = None
    status: Optional[TaskStatusEnum] = None
    priority: Optional[PriorityEnum] = None


class CareTaskCompleteRequest(BaseModel):
    actual_value: Optional[Dict[str, Any]] = None  # {"amount": 120, "unit": "ml"}
    notes: Optional[str] = None
    completed_by_name: Optional[str] = None
    occurred_at: Optional[str] = None


class TaskEscalateRequest(BaseModel):
    new_assignee_id: Optional[str] = None
    new_assignee_name: Optional[str] = None
    reason: Optional[str] = "Người phụ trách chính không phản hồi sau 30 phút"


class CareTaskResponse(BaseModel):
    id: str
    baby_id: str
    template_id: Optional[str] = None
    task_type: str
    title: str
    scheduled_time: str
    assigned_to: Optional[str] = None
    assigned_name: Optional[str] = None
    backup_assigned_to: Optional[str] = None
    backup_assigned_name: Optional[str] = None
    instructions: Optional[str] = None
    target_value: Optional[Dict[str, Any]] = None
    status: str
    priority: str
    created_by: str
    created_at: str
    completed_at: Optional[str] = None
    completed_by: Optional[str] = None
    actual_value: Optional[Dict[str, Any]] = None
    completion_notes: Optional[str] = None
    escalated_at: Optional[str] = None
    escalation_reason: Optional[str] = None


# ─── 3. CARE EVENT SCHEMAS ───────────────────────────────────────────────────

class CareEventCreate(BaseModel):
    baby_id: str
    event_type: TaskTypeEnum
    occurred_at: Optional[str] = None
    actual_value: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    task_id: Optional[str] = None


class CareEventResponse(BaseModel):
    id: str
    baby_id: str
    task_id: Optional[str] = None
    event_type: str
    occurred_at: str
    recorded_by: str
    recorded_by_name: str
    actual_value: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None
    synced_to_module: Optional[str] = None
    created_at: str


# ─── 4. DAILY SUMMARY SCHEMA ─────────────────────────────────────────────────

class CareTimelineSummary(BaseModel):
    baby_id: str
    date: str
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    handover_note: Optional[HandoverNoteResponse] = None
    tasks: List[CareTaskResponse] = Field(default_factory=list)
    recent_events: List[CareEventResponse] = Field(default_factory=list)
    ai_summary_text: Optional[str] = None


# ─── 5. WORKLOAD ANALYTICS SCHEMAS ───────────────────────────────────────────

class CaregiverWorkloadItem(BaseModel):
    caregiver_name: str
    assigned_tasks_count: int
    completed_tasks_count: int
    workload_percentage: float  # e.g. 55.0%
    completion_rate: float      # e.g. 90.0%


class WorkloadStatsResponse(BaseModel):
    baby_id: str
    period_days: int
    total_tasks_assigned: int
    total_tasks_completed: int
    caregivers_distribution: List[CaregiverWorkloadItem] = Field(default_factory=list)
    ai_rebalance_recommendation: Optional[str] = None
