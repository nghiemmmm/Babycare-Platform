"""
Care Coordination Router - Định nghĩa các API endpoints cho Sổ bàn giao và Lịch trình chăm sóc.
"""
from fastapi import APIRouter, Depends, Query, Path, status
from typing import List, Optional

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.care_coordination.schemas import (
    HandoverNoteCreate,
    HandoverNoteResponse,
    CareTaskCreate,
    CareTaskUpdate,
    CareTaskCompleteRequest,
    TaskEscalateRequest,
    CareTaskHandoffRequest,
    CareTaskClaimRequest,
    CareTaskResponse,
    CareEventCreate,
    CareEventResponse,
    CareTimelineSummary,
    WorkloadStatsResponse
)
from app.modules.care_coordination.service import CareCoordinationService

router = APIRouter(prefix="/care-coordination", tags=["Care Coordination & Handover"])

service = CareCoordinationService()


# ─── 1. HANDOVER NOTES ───────────────────────────────────────────────────────

@router.get("/handover/today", response_model=Optional[HandoverNoteResponse])
async def get_today_handover(
    baby_id: str = Query(..., description="Mã ID của bé"),
    date: Optional[str] = Query(None, description="Ngày cần tra cứu (YYYY-MM-DD), mặc định hôm nay"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Lấy lời dặn bàn giao trong ngày của bé từ phụ huynh."""
    return service.get_today_handover(baby_id, current_user.uid, date)


@router.post("/handover", response_model=HandoverNoteResponse, status_code=status.HTTP_201_CREATED)
async def save_handover_note(
    note_in: HandoverNoteCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """Tạo hoặc cập nhật lời dặn bàn giao buổi sáng cho người chăm sóc."""
    author_name = current_user.name or "Phụ huynh"
    return service.save_handover_note(note_in, current_user.uid, author_name)


# ─── 2. CARE TASKS ───────────────────────────────────────────────────────────

@router.get("/tasks/today", response_model=List[CareTaskResponse])
async def get_today_tasks(
    baby_id: str = Query(..., description="Mã ID của bé"),
    date: Optional[str] = Query(None, description="Ngày cần tra cứu (YYYY-MM-DD)"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Lấy danh sách các việc cần làm theo mốc giờ trong ngày của bé."""
    return service.get_today_tasks(baby_id, current_user.uid, date)


@router.post("/tasks", response_model=CareTaskResponse, status_code=status.HTTP_201_CREATED)
async def create_care_task(
    task_in: CareTaskCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """Bố mẹ tạo một việc cần làm cụ thể (gán người, đặt giờ, hướng dẫn)."""
    return service.create_care_task(task_in, current_user.uid)


@router.patch("/tasks/{task_id}/complete", response_model=CareTaskResponse)
async def complete_task(
    task_id: str = Path(..., description="Mã ID của việc cần làm"),
    complete_in: CareTaskCompleteRequest = CareTaskCompleteRequest(),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Người chăm sóc tick 1-chạm hoàn thành task kèm theo số liệu thực tế.
    Hệ thống tự động tạo CareEvent và đồng bộ sang Nutrition / Health Records.
    """
    user_name = current_user.name or "Người chăm sóc"
    return service.complete_task(task_id, complete_in, current_user.uid, user_name)


@router.post("/tasks/{task_id}/escalate", response_model=CareTaskResponse)
async def escalate_task(
    task_id: str = Path(..., description="Mã ID việc cần chuyển giao"),
    req: TaskEscalateRequest = TaskEscalateRequest(),
    current_user: UserRecord = Depends(get_current_user)
):
    """Chuyển giao task khẩn cấp cho người phụ trách dự phòng khi quá hạn."""
    return service.escalate_task(
        task_id=task_id,
        user_id=current_user.uid,
        new_assignee_id=req.new_assignee_id,
        new_assignee_name=req.new_assignee_name,
        reason=req.reason or "Quá hạn thực hiện"
    )


@router.patch("/tasks/{task_id}/handoff", response_model=CareTaskResponse)
async def handoff_task(
    task_id: str = Path(..., description="Mã ID việc cần chuyển giao"),
    req: CareTaskHandoffRequest = CareTaskHandoffRequest(new_assignee_name="Người chăm sóc"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Chuyển giao việc chăm sóc (Nhờ làm hộ tạm thời hoặc Đổi người phụ trách)."""
    return service.handoff_task(
        task_id=task_id,
        user_id=current_user.uid,
        new_assignee_name=req.new_assignee_name,
        is_temporary=req.is_temporary,
        reason=req.reason
    )


@router.patch("/tasks/{task_id}/claim", response_model=CareTaskResponse)
async def claim_task(
    task_id: str = Path(..., description="Mã ID việc cần nhận"),
    req: CareTaskClaimRequest = CareTaskClaimRequest(),
    current_user: UserRecord = Depends(get_current_user)
):
    """Người chăm sóc nhận một việc từ danh sách 'Ai rảnh'."""
    user_name = req.claimed_by_name or current_user.name or "Người chăm sóc"
    return service.claim_task(task_id, current_user.uid, user_name)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str = Path(..., description="Mã ID việc cần xóa"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Xóa một việc cần làm khỏi lịch."""
    service.delete_task(task_id, current_user.uid)
    return {"success": True, "message": "Đã xóa việc cần làm thành công"}


# ─── 3. TIMELINE & SUMMARY ───────────────────────────────────────────────────

@router.get("/overview", response_model=CareTimelineSummary)
@router.get("/summary/daily", response_model=CareTimelineSummary)
async def get_daily_timeline_summary(
    baby_id: str = Query(..., description="Mã ID của bé"),
    date: Optional[str] = Query(None, description="Ngày cần tổng hợp (YYYY-MM-DD)"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Lấy bức tranh tổng quan cả ngày: Lời dặn bàn giao, tiến độ tasks, và tóm tắt chăm sóc."""
    return service.get_timeline_summary(baby_id, current_user.uid, date)


# ─── 4. WORKLOAD ANALYTICS ───────────────────────────────────────────────────

@router.get("/workload-analytics", response_model=WorkloadStatsResponse)
async def get_workload_analytics(
    baby_id: str = Query(..., description="Mã ID của bé"),
    days: int = Query(7, ge=1, le=30, description="Số ngày cần phân tích (1-30 ngày)"),
    current_user: UserRecord = Depends(get_current_user)
):
    """Phân tích mức độ cân bằng khối lượng chăm sóc bé giữa các thành viên gia đình."""
    return service.get_workload_analytics(baby_id, current_user.uid, days)
