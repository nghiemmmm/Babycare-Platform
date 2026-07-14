"""
Baby Service Module

Handles business logic and permission checking for baby profiles.
"""
import logging
from datetime import datetime, timezone
from typing import Optional
from app.modules.baby.schemas import BabyCreate, BabyUpdate, BabyResponse
from app.modules.baby.repository import BabyRepository
from app.shared.exceptions import EntityNotFoundError, PermissionDeniedError

logger = logging.getLogger(__name__)

class BabyService:
    def __init__(self, repository: Optional[BabyRepository] = None):
        self.repository = repository or BabyRepository()

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
            guardians=[creator_id],
            created_at=now,
            updated_at=now
        )
        created_baby = self.repository.create(baby_obj)

        # Tự động sinh lịch tiêm chủng dự kiến cho bé
        try:
            from app.modules.vaccination.service import VaccinationService
            vaccination_service = VaccinationService(baby_service=self)
            vaccination_service.generate_default_schedule(created_baby.id, created_baby.birth_date)
        except Exception as e:
            logger.error(f"Failed to generate default vaccine schedule for baby {created_baby.id}: {e}")
            raise e

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
        baby = self.repository.get(baby_id)
        if not baby:
            raise EntityNotFoundError("Không tìm thấy hồ sơ của bé")
        
        if user_id not in baby.guardians:
            raise PermissionDeniedError("Bạn không có quyền truy cập hồ sơ bé này")
            
        return baby

    def get_my_babies(self, user_id: str) -> list[BabyResponse]:
        """
        Lấy danh sách các bé thuộc quyền giám hộ của người dùng.

        Args:
            user_id: UID của người giám hộ.

        Returns:
            Danh sách các em bé.
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
        
        data = baby_update.model_dump(exclude_unset=True)
        updated_baby = self.repository.update(baby_id, data)
        if not updated_baby:
            raise EntityNotFoundError("Cập nhật hồ sơ thất bại")
            
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
        return self.repository.delete(baby_id)
