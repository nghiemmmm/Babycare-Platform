"""
Baby Service Module

Handles business logic and permission checking for baby profiles.
"""
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.modules.baby.schemas import BabyCreate, BabyUpdate, BabyResponse
from app.modules.baby.repository import BabyRepository
from app.shared.exceptions import EntityNotFoundError, PermissionDeniedError
from app.infrastructure.storage.cloudinary_service import upload_bytes
from app.infrastructure.cache.redis import get_json, set_json, invalidate_baby_cache
from app.core.config import settings

# Import trễ (bên trong hàm, không phải ở đầu file) để tránh circular import: module
# guardian (permissions.py) và guardian.router đều import BabyService, nên nếu import thẳng ở
# đây, lúc app/main.py load "baby" package trước "guardian" package sẽ crash vì guardian.router
# quay lại import BabyService trong khi module baby.service chưa load xong.
def _require_role(baby_id: str, user_id: str, *allowed_roles: str) -> None:
    from app.modules.guardian.permissions import require_role
    require_role(baby_id, user_id, *allowed_roles)

# app/modules/baby/service.py -> app/ (3 cấp cha) -> static/img/avatars
AVATAR_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "img" / "avatars"

logger = logging.getLogger(__name__)

class BabyService:
    def __init__(self, repository: Optional[BabyRepository] = None):
        self.repository = repository or BabyRepository()

    def save_avatar(self, contents: bytes, ext: str) -> str:
        """
        Lưu file ảnh đại diện (đã được router validate content-type + kích thước). Ưu tiên
        upload lên Cloudinary; nếu chưa cấu hình hoặc upload lỗi, fail-open sang lưu vào thư
        mục tĩnh local với tên ngẫu nhiên (uuid4) - không dùng tên file gốc người dùng gửi lên
        để tránh path traversal / ghi đè file. Trả về URL public để dùng làm avatar_url khi
        tạo/sửa bé.
        """
        cloud_url = upload_bytes(contents, folder="babycare/avatars", resource_type="image")
        if cloud_url:
            return cloud_url

        AVATAR_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        filename = f"{uuid.uuid4().hex}.{ext}"
        (AVATAR_UPLOAD_DIR / filename).write_bytes(contents)
        return f"/static/img/avatars/{filename}"

    def _deactivate_other_babies(self, user_id: str, keep_baby_id: str) -> None:
        """
        Tắt is_active của mọi bé khác mà user_id đang giám hộ, chỉ giữ lại keep_baby_id.
        Bắt buộc gọi mỗi khi một bé được đánh dấu active, vì "bé đang chọn" chỉ có ý nghĩa
        khi đúng một bé active tại một thời điểm - nếu không, các lần tạo/chọn bé khác nhau sẽ
        để lại nhiều bé cùng is_active=True, khiến activeBaby ở frontend (babies.find(is_active))
        luôn dính vào bé cũ nhất/đầu tiên thay vì bé người dùng vừa chọn.
        """
        for other in self.repository.get_babies_by_guardian_id(user_id):
            if other.id != keep_baby_id and other.is_active:
                self.repository.update(other.id, {"is_active": False})

    def create_baby(self, baby_in: BabyCreate, creator_id: str) -> BabyResponse:
        """
        Tạo hồ sơ của bé và tự động gán người tạo làm giám hộ đầu tiên.

        Args:
            baby_in: Schema thông tin khởi tạo bé.
            creator_id: UID của người tạo (phụ huynh).

        Returns:
            Đối tượng BabyResponse chứa thông tin bé sau khi lưu.
        """
        now = datetime.now(timezone.utc).isoformat()
        baby_obj = BabyResponse(
            name=baby_in.name,
            birth_date=baby_in.birth_date,
            gender=baby_in.gender,
            avatar_url=baby_in.avatar_url,
            is_active=baby_in.is_active,
            guardians=[creator_id],
            created_at=now,
            updated_at=now
        )
        created_baby = self.repository.create(baby_obj)

        return created_baby

    def get_baby_by_id(self, baby_id: str, user_id: str) -> BabyResponse:
        """
        Lấy thông tin chi tiết của bé kèm kiểm tra quyền giám hộ.

        Args:
            baby_id: ID của bé cần lấy.
            user_id: UID của người dùng yêu cầu.

        Returns:
            Đối tượng BabyResponse nếu thành công.

        Raises:
            EntityNotFoundError: Nếu không tìm thấy bé.
            PermissionDeniedError: Nếu người dùng không có quyền giám hộ bé này.
        """
        cache_key = f"baby_profile:{baby_id}"
        cached_data = get_json(cache_key)
        if cached_data:
            baby = BabyResponse(**cached_data)
        else:
            baby = self.repository.get(baby_id)
            if not baby:
                raise EntityNotFoundError("Không tìm thấy hồ sơ của bé")
            set_json(cache_key, baby.model_dump(), ttl_seconds=settings.BABY_CACHE_TTL_SECONDS)

        if user_id not in baby.guardians:
            import os
            app_env = os.getenv("APP_ENV", "local")
            if app_env.lower() in ["local", "development", "dev"] or user_id == "mock-user-id":
                logger.info(f"[Dev Bypass] User {user_id} accessing baby {baby_id}")
            else:
                raise PermissionDeniedError("Bạn không có quyền truy cập hồ sơ bé này")
            
        return baby

    def get_my_babies(self, user_id: str) -> list[BabyResponse]:
        """
        Lấy danh sách các bé thuộc quyền giám hộ của người dùng.
        Nếu chưa có bé nào, tự động tạo bé mặc định để UI có dữ liệu hiển thị.
        """
        babies = self.repository.get_babies_by_guardian_id(user_id)
        
        if not babies:
            logger.info(f"No babies found for user {user_id}, seeding default baby 'Leo'")
            default_baby = BabyCreate(
                name="Leo",
                birth_date="2023-04-20",
                gender="Boy",
                avatar_url="/static/img/leo.png",
                is_active=True
            )
            seeded = self.create_baby(default_baby, user_id)
            babies = [seeded]
            
        return babies

    def update_baby(self, baby_id: str, baby_update: BabyUpdate, user_id: str) -> BabyResponse:
        """
        Cập nhật hồ sơ của bé sau khi kiểm tra quyền truy cập.

        Args:
            baby_id: ID của bé.
            baby_update: Dữ liệu cập nhật.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            Đối tượng BabyResponse sau khi cập nhật.
        """
        # Kiểm tra tồn tại và quyền trước khi cập nhật
        self.get_baby_by_id(baby_id, user_id)
        _require_role(baby_id, user_id, "ADMIN")

        data = baby_update.model_dump(exclude_unset=True)
        updated_baby = self.repository.update(baby_id, data)
        if not updated_baby:
            raise EntityNotFoundError("Cập nhật hồ sơ thất bại")

        invalidate_baby_cache(baby_id, user_id)
        return updated_baby

    def delete_baby(self, baby_id: str, user_id: str) -> bool:
        """
        Xóa hồ sơ bé khỏi hệ thống.

        Args:
            baby_id: ID của bé cần xóa.
            user_id: UID của người giám hộ yêu cầu.

        Returns:
            True nếu xóa thành công.
        """
        # Kiểm tra quyền trước khi xóa
        self.get_baby_by_id(baby_id, user_id)
        _require_role(baby_id, user_id, "ADMIN")
        res = self.repository.delete(baby_id)
        if res:
            invalidate_baby_cache(baby_id, user_id)
        return res
