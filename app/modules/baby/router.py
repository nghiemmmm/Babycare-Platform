"""
Baby Router Module

Defines HTTP API endpoints for managing baby profiles.
"""
from fastapi import APIRouter, Depends, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.baby.schemas import BabyCreate, BabyUpdate, BabyResponse
from app.modules.baby.service import BabyService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Babies"])
baby_service = BabyService()

@router.post("/", response_model=BabyResponse, status_code=status.HTTP_201_CREATED)
async def create_new_baby(
    baby_in: BabyCreate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Tạo mới một hồ sơ em bé.
    Người tạo sẽ tự động được gán làm người giám hộ chính.
    """
    return baby_service.create_baby(baby_in, creator_id=current_user.uid)

@router.get("/", response_model=list[BabyResponse])
async def list_babies(
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy danh sách tất cả các em bé mà người dùng hiện tại có quyền giám hộ.
    """
    return baby_service.get_my_babies(user_id=current_user.uid)

@router.get("/{baby_id}", response_model=BabyResponse)
async def get_baby_details(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Lấy thông tin chi tiết một em bé (Yêu cầu phải có quyền giám hộ).
    """
    return baby_service.get_baby_by_id(baby_id, user_id=current_user.uid)

@router.put("/{baby_id}", response_model=BabyResponse)
async def update_baby_details(
    baby_id: str,
    baby_update: BabyUpdate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cập nhật hồ sơ em bé (Yêu cầu phải có quyền giám hộ).
    """
    return baby_service.update_baby(baby_id, baby_update, user_id=current_user.uid)

@router.delete("/{baby_id}", response_model=Message)
async def remove_baby_profile(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Xóa hồ sơ em bé khỏi hệ thống (Yêu cầu phải có quyền giám hộ).
    """
    baby_service.delete_baby(baby_id, user_id=current_user.uid)
    return Message(message="Xóa hồ sơ bé thành công")
