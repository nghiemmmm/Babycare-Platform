"""
Kiểm tra vai trò (role) của một user trên một bé cụ thể - dùng để giới hạn các thao tác
ghi/xoá dữ liệu đúng theo đúng phạm vi ADMIN / GUARDIAN / VIEWER đã chọn lúc mời (xem
GuardianInvite.role). Trước đây guardians[] trên baby document chỉ được dùng để kiểm tra CÓ
quyền truy cập hay không (mọi vai trò như nhau) - module này bổ sung lớp kiểm tra thứ hai:
có quyền truy cập nhưng vai trò gì.
"""
from app.modules.baby.repository import BabyRepository
from app.modules.guardian.repository import GuardianRepository
from app.shared.exceptions import PermissionDeniedError

ADMIN = "ADMIN"
GUARDIAN = "GUARDIAN"
VIEWER = "VIEWER"

_baby_repo = BabyRepository()
_guardian_repo = GuardianRepository()


def get_role_for_user(baby_id: str, user_id: str) -> str:
    """
    Trả về vai trò của user trên bé. Ưu tiên bản ghi guardian thật (collection "guardians");
    nếu user nằm trong babies.guardians[] nhưng chưa có bản ghi guardian riêng (trường hợp chủ
    sở hữu đầu tiên, trước khi GET /guardians tự tạo bản ghi ADMIN mặc định), coi như ADMIN.
    """
    guardian = _guardian_repo.get_guardian_by_baby_and_user(baby_id, user_id)
    if guardian:
        return guardian.get("role", GUARDIAN)

    baby = _baby_repo.get(baby_id)
    if baby and user_id in getattr(baby, "guardians", []):
        return ADMIN

    raise PermissionDeniedError("Bạn không có quyền truy cập hồ sơ bé này")


def require_role(baby_id: str, user_id: str, *allowed_roles: str) -> None:
    """Raise PermissionDeniedError (HTTP 403) nếu vai trò của user trên bé không nằm trong
    allowed_roles. Gọi sau bước kiểm tra quyền truy cập thông thường (vd. get_baby_by_id)."""
    role = get_role_for_user(baby_id, user_id)
    if role not in allowed_roles:
        if role == VIEWER:
            raise PermissionDeniedError("Vai trò Người xem chỉ được xem dữ liệu, không thể ghi/sửa/xoá")
        raise PermissionDeniedError("Vai trò của bạn không đủ quyền thực hiện thao tác này")
