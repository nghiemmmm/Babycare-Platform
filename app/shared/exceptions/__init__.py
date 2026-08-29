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


class UpstreamTimeoutError(AppException):
    """Ngoại lệ xảy ra khi thao tác với hệ thống bên ngoài (Firebase/Firestore) vượt quá thời gian chờ cho phép."""
    def __init__(self, message: str = "Hệ thống xử lý quá lâu, vui lòng thử lại sau."):
        self.message = message
        super().__init__(self.message)


class EmailAlreadyExistsError(AppException):
    """Ngoại lệ xảy ra khi đăng ký với email đã tồn tại trong hệ thống."""
    def __init__(self, message: str = "Email đã được sử dụng."):
        self.message = message
        super().__init__(self.message)


class InvalidCredentialsError(AppException):
    """Ngoại lệ xảy ra khi đăng nhập với email hoặc mật khẩu không đúng."""
    def __init__(self, message: str = "Email hoặc mật khẩu không đúng."):
        self.message = message
        super().__init__(self.message)


class InvalidRegistrationDataError(AppException):
    """Ngoại lệ xảy ra khi dữ liệu đăng ký không hợp lệ (tên đăng nhập/mật khẩu sai định dạng Firebase yêu cầu)."""
    def __init__(self, message: str = "Dữ liệu đăng ký không hợp lệ."):
        self.message = message
        super().__init__(self.message)


class InvalidPasswordResetCodeError(AppException):
    """Ngoại lệ xảy ra khi mã OTP đặt lại mật khẩu không đúng, đã hết hạn, hoặc đã bị dùng/thử sai quá số lần cho phép."""
    def __init__(self, message: str = "Mã xác thực không đúng hoặc đã hết hạn, vui lòng yêu cầu gửi lại mã mới."):
        self.message = message
        super().__init__(self.message)


class RateLimitExceededError(AppException):
    """Ngoại lệ xảy ra khi một client vượt quá số lần thử cho phép trong khoảng thời gian quy định."""
    def __init__(self, message: str = "Bạn đã thực hiện quá nhiều yêu cầu. Vui lòng thử lại sau.", retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class AIGenerationError(AppException):
    """Ngoại lệ xảy ra khi mô hình AI không tạo được nội dung hợp lệ (lỗi gọi model hoặc lỗi parse kết quả)."""
    def __init__(self, message: str = "Không thể tạo gợi ý dinh dưỡng lúc này, vui lòng thử lại sau."):
        self.message = message
        super().__init__(self.message)


class MealPlanLockedError(AppException):
    """Ngoại lệ xảy ra khi cố tạo thực đơn tuần mới trong lúc thực đơn hiện tại đã được chấp nhận và chưa hết hạn 7 ngày."""
    def __init__(self, message: str = "Thực đơn tuần hiện tại đang được áp dụng, chưa thể tạo mới."):
        self.message = message
        super().__init__(self.message)
