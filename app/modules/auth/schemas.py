from pydantic import BaseModel
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
    username: str
    email: Optional[str] = None
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
    Schema dùng cho yêu cầu cập nhật thông tin hồ sơ.
    """
    username: Optional[str] = None
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

