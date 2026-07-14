"""
Shared Exceptions Module

Defines base application and domain exceptions.
"""

class AppException(Exception):
    """Ngoại lệ cơ sở của toàn ứng dụng (Base Application Exception)."""
    pass


class EntityNotFoundError(AppException):
    """Ngoại lệ xảy ra khi không tìm thấy thực thể trong cơ sở dữ liệu."""
    def __init__(self, message: str = "Tài nguyên không tồn tại"):
        self.message = message
        super().__init__(self.message)


class PermissionDeniedError(AppException):
    """Ngoại lệ xảy ra khi người dùng không có quyền truy cập tài nguyên."""
    def __init__(self, message: str = "Bạn không có quyền thực hiện hành động này"):
        self.message = message
        super().__init__(self.message)
