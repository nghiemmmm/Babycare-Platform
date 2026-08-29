"""
Medication Tracking Router Module

Defines HTTP API endpoints for managing baby structured medication plans, dose checklist, and legacy logs.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, status, Query
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.medication.schemas import (
    MedicationLogCreate,
    MedicationLogResponse,
    MedicationPlanCreate,
    MedicationPlanUpdate,
    MedicationPlanResponse,
    MedicationDoseLogCreate,
    MedicationDoseLogResponse,
    TodayDoseItem
)
from app.modules.medication.service import MedicationService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Medication Tracking & Management"])
med_service = MedicationService()


# ============================================================================
# 1. STRUCTURED MEDICATION PLANS (Đơn thuốc / Phác đồ)
# ============================================================================

@router.post("/{baby_id}/medication-plans", response_model=MedicationPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_baby_medication_plan(
    baby_id: str,
    plan_in: MedicationPlanCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Tạo một đơn thuốc mới có cấu trúc 12 trường y khoa cho bé (Yêu cầu quyền giám hộ).
    """
    return med_service.create_medication_plan(baby_id, plan_in, user_id=current_user.uid)


@router.get("/{baby_id}/medication-plans", response_model=List[MedicationPlanResponse])
async def get_baby_medication_plans(
    baby_id: str,
    status_filter: Optional[str] = Query(None, description="Lọc theo trạng thái: active | completed | paused"),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy danh sách các đơn thuốc của bé (Yêu cầu quyền giám hộ).
    """
    return med_service.get_medication_plans(baby_id, user_id=current_user.uid, status_filter=status_filter)


@router.get("/{baby_id}/medication-plans/{plan_id}", response_model=MedicationPlanResponse)
async def get_baby_medication_plan_detail(
    baby_id: str,
    plan_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy chi tiết một đơn thuốc của bé.
    """
    return med_service.get_medication_plan_by_id(baby_id, plan_id, user_id=current_user.uid)


@router.patch("/{baby_id}/medication-plans/{plan_id}", response_model=MedicationPlanResponse)
async def update_baby_medication_plan(
    baby_id: str,
    plan_id: str,
    update_in: MedicationPlanUpdate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cập nhật thông tin hoặc trạng thái đơn thuốc (active / completed / paused).
    """
    return med_service.update_medication_plan(baby_id, plan_id, update_in, user_id=current_user.uid)


@router.delete("/{baby_id}/medication-plans/{plan_id}", response_model=Message)
async def delete_baby_medication_plan(
    baby_id: str,
    plan_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một đơn thuốc khỏi tủ thuốc của bé.
    """
    med_service.delete_medication_plan(baby_id, plan_id, user_id=current_user.uid)
    return Message(message="Đã xóa đơn thuốc thành công")


# ============================================================================
# 2. TODAY'S DOSE CHECKLIST & LOGGING (Checklist cữ uống hôm nay)
# ============================================================================

@router.get("/{baby_id}/medication-doses/today", response_model=List[TodayDoseItem])
async def get_baby_today_doses(
    baby_id: str,
    target_date: Optional[str] = Query(None, description="Ngày cần xem cữ thuốc (YYYY-MM-DD), mặc định là hôm nay"),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy checklist các cữ thuốc hôm nay, phân chia theo buổi (Sáng, Trưa, Tối, Khi cần).
    """
    return med_service.get_today_doses(baby_id, user_id=current_user.uid, target_date_str=target_date)


@router.post("/{baby_id}/medication-doses/log", response_model=MedicationDoseLogResponse, status_code=status.HTTP_201_CREATED)
async def log_baby_dose_action(
    baby_id: str,
    log_in: MedicationDoseLogCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận phụ huynh đã cho bé uống thuốc hoặc bỏ qua cữ thuốc (1-Tap Mark Taken/Skipped).
    """
    return med_service.log_dose_action(baby_id, log_in, user_id=current_user.uid)


@router.get("/{baby_id}/medication-doses/history", response_model=List[MedicationDoseLogResponse])
async def get_baby_dose_history(
    baby_id: str,
    limit: int = Query(200, ge=1, le=500),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử các cữ uống thuốc đã ghi nhận.
    """
    return med_service.get_dose_history(baby_id, user_id=current_user.uid, limit=limit)


# ============================================================================
# 3. LEGACY ENDPOINTS (Tương thích ngược)
# ============================================================================

@router.post("/{baby_id}/medication", response_model=MedicationLogResponse, status_code=status.HTTP_201_CREATED)
async def add_medication_log(
    baby_id: str,
    log_in: MedicationLogCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận một bản ghi nhật ký dùng thuốc/vitamin mới cho bé (Yêu cầu quyền giám hộ).
    """
    return med_service.add_medication_log(baby_id, log_in, user_id=current_user.uid)


@router.get("/{baby_id}/medication", response_model=list[MedicationLogResponse])
async def get_medication_history(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy toàn bộ lịch sử dùng thuốc/vitamin của bé (Yêu cầu quyền giám hộ).
    """
    return med_service.get_medication_history(baby_id, user_id=current_user.uid)


@router.delete("/{baby_id}/medication/{log_id}", response_model=Message)
async def delete_medication_log(
    baby_id: str,
    log_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa một bản ghi nhật ký dùng thuốc/vitamin của bé (Yêu cầu quyền giám hộ).
    """
    med_service.delete_medication_log(baby_id, log_id, user_id=current_user.uid)
    return Message(message="Xóa nhật ký dùng thuốc thành công")



# Router mới cho Sức khoẻ & Thuốc theo giao diện Frontend
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone

health_medication_router = APIRouter(prefix="/health", tags=["Health & Medication"])

from app.modules.medication.schemas import (
    SafetyAlert,
    CountdownWidget,
    HealthDashboardResponse,
    AdministerMedicationRequest,
    AdministerMedicationResponse
)

@health_medication_router.get("/dashboard", response_model=HealthDashboardResponse)
async def get_health_dashboard(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy trạng thái cảnh báo an toàn thuốc và đếm ngược liều dùng tiếp theo.
    """
    history = med_service.get_medication_history(baby_id, user_id=current_user.uid)
    
    # Tìm liều Paracetamol gần nhất
    paracetamol_logs = [log for log in history if "paracetamol" in log.medication_name.lower() or "hapacol" in log.medication_name.lower()]
    
    if not paracetamol_logs:
        # Mặc định bình thường nếu chưa uống thuốc gì
        return HealthDashboardResponse(
            safety_alert=SafetyAlert(level="NORMAL", message="Không có cảnh báo đặc biệt về thuốc. Hãy cho bé uống đúng theo hướng dẫn."),
            countdown_widget=None
        )
        
    last_log = paracetamol_logs[0]
    try:
        last_time = datetime.fromisoformat(last_log.logged_at.replace("Z", "+00:00"))
    except Exception:
        last_time = datetime.now(timezone.utc)
        
    next_eligible = last_time + timedelta(hours=4)
    now = datetime.now(timezone.utc)
    
    is_disabled = now < next_eligible
    
    # Định dạng hiển thị giờ địa phương
    last_time_str = last_time.astimezone().strftime("%I:%M %p")
    next_eligible_str = next_eligible.isoformat()
    
    if is_disabled:
        alert = SafetyAlert(
            level="CRITICAL",
            message=f"{last_log.medication_name} uống lúc {last_time_str}. Tuyệt đối không cho uống thêm trước {next_eligible.astimezone().strftime('%I:%M %p')}!"
        )
    else:
        alert = SafetyAlert(
            level="NORMAL",
            message=f"Đã đủ 4 tiếng kể từ liều {last_log.medication_name} gần nhất. Bạn có thể cho uống liều tiếp theo nếu bé sốt lại."
        )
        
    return HealthDashboardResponse(
        safety_alert=alert,
        countdown_widget=CountdownWidget(
            medication_name=last_log.medication_name,
            next_eligible_time=next_eligible_str,
            is_administer_disabled=is_disabled
        )
    )

@health_medication_router.post("/medications/administer", response_model=AdministerMedicationResponse)
async def administer_medication(
    req: AdministerMedicationRequest,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Ghi nhận lịch sử cho bé uống thuốc thực tế và trả về đếm ngược.
    """
    log_in = MedicationLogCreate(
        logged_at=req.administered_at,
        medication_name=req.medication_name,
        dosage=req.amount,
        prescribed_by="Bác sĩ Nhi kê đơn",
        notes="Ghi nhận qua giao diện an toàn sức khỏe"
    )
    
    med_service.add_medication_log(req.baby_id, log_in, user_id=current_user.uid)
    
    try:
        admin_time = datetime.fromisoformat(req.administered_at.replace("Z", "+00:00"))
    except Exception:
        admin_time = datetime.now(timezone.utc)
        
    next_dose = admin_time + timedelta(hours=4)
    now = datetime.now(timezone.utc)
    
    countdown = max(0, int((next_dose - now).total_seconds()))
    
    return AdministerMedicationResponse(
        success=True,
        next_scheduled_dosage=next_dose.isoformat(),
        countdown_seconds=countdown
    )
