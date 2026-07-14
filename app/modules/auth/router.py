from fastapi import APIRouter, Depends
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord, UserMeResponse, UserProfileUpdate, UserProfileResponse
from app.modules.auth.service import get_or_create_user_profile, update_user_profile

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.get("/me", response_model=UserMeResponse)
async def get_my_profile(current_user: UserRecord = Depends(get_current_user)):
    """
    Lấy thông tin hồ sơ của người dùng hiện tại đang đăng nhập.
    Tự động khởi tạo thông tin trống trong Firestore ở lần đăng nhập đầu tiên.
    """
    profile = get_or_create_user_profile(current_user)
    return {
        "uid": current_user.uid,
        "email": current_user.email,
        "name": current_user.name,
        "picture": current_user.picture,
        "profile": profile
    }

@router.put("/me", response_model=UserProfileResponse)
async def update_my_profile(
    update_data: UserProfileUpdate,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Cập nhật thông tin hồ sơ người dùng trong Firestore (username, phone).
    """
    # Convert Pydantic object sang dict và loại bỏ các giá trị không được truyền lên (unset)
    data = update_data.model_dump(exclude_unset=True)
    updated_profile = update_user_profile(current_user.uid, data)
    return updated_profile

