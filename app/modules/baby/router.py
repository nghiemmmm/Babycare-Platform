"""
Baby Router Module

Defines HTTP API endpoints for managing baby profiles.
"""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserRecord
from app.modules.baby.schemas import AvatarUploadResponse, BabyCreate, BabyUpdate, BabyResponse
from app.modules.baby.service import BabyService
from app.shared.schemas import Message

router = APIRouter(prefix="/babies", tags=["Babies"])
baby_service = BabyService()

# Content-type -> phần mở rộng file lưu trên đĩa. Chỉ nhận ảnh, không suy ra đuôi file từ tên
# gốc người dùng gửi lên (tránh path traversal / giả mạo đuôi file thực thi được).
_ALLOWED_AVATAR_TYPES = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "image/gif": "gif"}
_MAX_AVATAR_SIZE_BYTES = 5 * 1024 * 1024  # 5MB

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

@router.post("/upload-avatar", response_model=AvatarUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_baby_avatar(
    file: UploadFile = File(..., description="Ảnh đại diện của bé (JPG/PNG/WEBP/GIF, tối đa 5MB)"),
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Tải ảnh đại diện của bé lên server, trả về URL tĩnh để dùng làm avatar_url khi tạo/sửa hồ
    sơ. Tách riêng khỏi create/update vì lúc tạo bé mới chưa có baby_id để gắn ảnh vào.
    """
    ext = _ALLOWED_AVATAR_TYPES.get(file.content_type or "")
    if not ext:
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận ảnh định dạng JPG, PNG, WEBP hoặc GIF.")

    contents = await file.read()
    if len(contents) > _MAX_AVATAR_SIZE_BYTES:
        raise HTTPException(status_code=400, detail="Ảnh vượt quá dung lượng cho phép (tối đa 5MB).")
    if not contents:
        raise HTTPException(status_code=400, detail="File ảnh trống.")

    avatar_url = baby_service.save_avatar(contents, ext)
    return AvatarUploadResponse(avatar_url=avatar_url)

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

@router.patch("/{baby_id}/set-active", response_model=BabyResponse)
async def set_active_baby(
    baby_id: str,
    current_user: UserRecord = Depends(get_current_user)
):
    """
    Đánh dấu một hồ sơ bé là "đang chọn" - tự động bỏ chọn mọi bé khác của người dùng.
    """
    return baby_service.set_active_baby(baby_id, user_id=current_user.uid)

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
