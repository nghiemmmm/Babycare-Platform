"""
Async Jobs Status Router Module

Cung cấp HTTP API cho phép Frontend polling tra cứu tiến trình các tác vụ xử lý nền cho bé.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Any, Dict

from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.shared.jobs import JobManager, JobStatus
from app.shared.exceptions import EntityNotFoundError

jobs_router = APIRouter(prefix="/jobs", tags=["Async Jobs"])


class JobStatusResponse(BaseModel):
    job_id: str
    job_type: Optional[str] = None
    status: JobStatus
    progress: int = 0
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@jobs_router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Tra cứu tiến trình thực hiện tác vụ chạy nền (Tạo thực đơn, xuất báo cáo...).
    """
    job_data = JobManager.get_job(job_id)
    if not job_data:
        raise EntityNotFoundError("Không tìm thấy thông tin tiến trình xử lý cho bé.")

    # Kiểm tra quyền sở hữu job nếu có user_id
    job_user_id = job_data.get("user_id")
    if job_user_id and job_user_id != current_user.uid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Bạn không có quyền xem thông tin tiến trình này."
        )

    return JobStatusResponse(
        job_id=job_data.get("job_id", job_id),
        job_type=job_data.get("job_type"),
        status=JobStatus(job_data.get("status", JobStatus.PENDING.value)),
        progress=job_data.get("progress", 0),
        result=job_data.get("result"),
        error=job_data.get("error"),
        created_at=job_data.get("created_at"),
        updated_at=job_data.get("updated_at")
    )
