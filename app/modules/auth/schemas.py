from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserRecord(BaseModel):
    """
    Dữ liệu được giải mã và xác thực từ Firebase ID Token.
    """
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class UserProfileBase(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    role: str = "USER"
    active: bool = True
    first_login: bool = True


class UserProfileResponse(UserProfileBase):
    """
    Cấu trúc dữ liệu hồ sơ người dùng lưu trong Firestore database.
    """
    created_at: str
    updated_at: str
    last_login_at: Optional[str] = None
    phone: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """
    Schema dùng cho yêu cầu cập nhật thông tin hồ sơ. Đổi email đăng nhập không nằm trong
    phạm vi endpoint này (đổi email Firebase Auth cần luồng xác minh riêng) - chỉ đổi được
    tên hiển thị và số điện thoại.
    """
    name: Optional[str] = None
    phone: Optional[str] = None


class UserMeResponse(BaseModel):
    """
    Schema trả về cho endpoint /auth/me kết hợp thông tin Firebase Auth và Firestore Profile.
    """
    uid: str
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None
    profile: Optional[UserProfileResponse] = None


class RegisterRequest(BaseModel):
    """
    Schema cho yêu cầu đăng ký tài khoản mới qua Firebase Authentication.
    """
    email: EmailStr
    password: str = Field(min_length=6)
    name: Optional[str] = None


class LoginRequest(BaseModel):
    """
    Schema cho yêu cầu đăng nhập bằng email/mật khẩu qua Firebase Authentication.
    """
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """
    Schema cho yêu cầu làm mới ID token bằng refresh token.
    """
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    """
    Schema cho yêu cầu gửi mã OTP đặt lại mật khẩu qua email.
    """
    email: EmailStr


class VerifyOtpRequest(BaseModel):
    """
    Schema cho yêu cầu kiểm tra mã OTP đúng hay không, trước khi cho phép nhập mật khẩu mới.
    """
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ResetPasswordRequest(BaseModel):
    """
    Schema cho yêu cầu xác nhận đặt lại mật khẩu bằng mã OTP 6 chữ số nhận qua email.
    """
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_password: str = Field(min_length=6)


class AuthTokenResponse(BaseModel):
    """
    Schema trả về sau khi đăng ký/đăng nhập/refresh thành công.
    """
    uid: str
    email: Optional[str] = None
    id_token: str
    refresh_token: str
    expires_in: int
