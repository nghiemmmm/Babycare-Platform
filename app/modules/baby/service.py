"""
Baby Service Module

Handles business logic and permission checking for baby profiles.
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from app.modules.baby.schemas import BabyCreate, BabyUpdate, BabyResponse
from app.modules.baby.repository import BabyRepository
from app.shared.exceptions import EntityNotFoundError, PermissionDeniedError
from app.infrastructure.storage.cloudinary_service import upload_bytes

# Import trễ (bên trong hàm, không phải ở đầu file) để tránh circular import: module
# guardian (permissions.py) và guardian.router đều import BabyService, nên nếu import thẳng ở
# đây, lúc app/main.py load "baby" package trước "guardian" package sẽ crash vì guardian.router
# quay lại import BabyService trong khi module baby.service chưa load xong.
def _require_role(baby_id: str, user_id: str, *allowed_roles: str) -> None:
    from app.modules.guardian.permissions import require_role
    require_role(baby_id, user_id, *allowed_roles)

# app/modules/baby/service.py -> app/ (3 cấp cha) -> static/img/avatars
AVATAR_UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "static" / "img" / "avatars"

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
            blood_type=baby_in.blood_type,
            pediatrician_name=baby_in.pediatrician_name,
            allergies=baby_in.allergies,
            guardians=[creator_id],
            created_at=now,
            updated_at=now
        )
        created_baby = self.repository.create(baby_obj)

        if created_baby.is_active:
            self._deactivate_other_babies(creator_id, created_baby.id)

        return created_baby

    def set_active_baby(self, baby_id: str, user_id: str) -> BabyResponse:
        """
        Đánh dấu baby_id là bé đang chọn (active) của user_id, tự động bỏ active mọi bé
        khác - dùng khi người dùng chuyển đổi giữa các hồ sơ bé trên UI.
        """
        self.get_baby_by_id(baby_id, user_id)  # kiểm tra tồn tại + quyền
        self._deactivate_other_babies(user_id, baby_id)
        updated = self.repository.update(baby_id, {"is_active": True})
        if not updated:
            raise EntityNotFoundError("Không thể chọn hồ sơ bé này")
        return updated

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
        baby = self.repository.get(baby_id)
        if not baby:
            raise EntityNotFoundError("Không tìm thấy hồ sơ của bé")
        
        if user_id not in baby.guardians:
            raise PermissionDeniedError("Bạn không có quyền truy cập hồ sơ bé này")
            
        return baby

    def get_my_babies(self, user_id: str) -> list[BabyResponse]:
        """
        Lấy danh sách các bé thuộc quyền giám hộ của người dùng. Trả về mảng rỗng nếu
        chưa có bé nào - đây là tín hiệu để frontend đưa người dùng vào luồng onboarding
        tạo hồ sơ bé đầu tiên (xem App.tsx), nên không được tự seed dữ liệu giả ở đây.
        """
        return self.repository.get_babies_by_guardian_id(user_id)

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

        if data.get("is_active"):
            self._deactivate_other_babies(user_id, baby_id)

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
        return self.repository.delete(baby_id)
